# ==============================================================================
# GBA Super Smash Bros. Demake Makefile
# Compatible with devkitARM & libtonc
# ==============================================================================

# Ensure DEVKITARM is configured
ifeq ($(strip $(DEVKITARM)),)
  # Default paths for standard devkitPro installations
  ifneq ($(wildcard C:/devkitPro/devkitARM),)
    DEVKITARM := C:/devkitPro/devkitARM
  else ifneq ($(wildcard /opt/devkitpro/devkitARM),)
    DEVKITARM := /opt/devkitpro/devkitARM
  else
    $(error "DEVKITARM environment variable is not defined. Please install devkitPro/devkitARM and try again.")
  endif
endif

DEVKITPRO ?= $(shell dirname "$(DEVKITARM)")

# Cross-compilation Prefix
PREFIX  := $(DEVKITARM)/bin/arm-none-eabi-
CC      := $(PREFIX)gcc
OBJCOPY := $(PREFIX)objcopy
GBAFIX  := $(DEVKITPRO)/tools/bin/gbafix

# Target rom name
TARGET  := gba_3d

# Sources and Objects
SOURCES := main.c engine3d.c render.c models.c stadium.c link.c achievements.c
OBJS    := $(SOURCES:.c=.o)

# GBA ARM7TDMI Architecture compiler flags
# -mthumb            : Use space-efficient 16-bit Thumb instruction set
# -mthumb-interwork   : Enable interworking between Thumb & ARM mode instructions
# -mcpu=arm7tdmi      : Target specific architecture core
ARCH    := -mthumb -mthumb-interwork -mcpu=arm7tdmi
CFLAGS  := $(ARCH) -O2 -Wall -fno-strict-aliasing
LDFLAGS := $(ARCH) -specs=gba.specs

# Library & Include Config
CFLAGS  += -I$(DEVKITPRO)/libtonc/include
LDFLAGS += -L$(DEVKITPRO)/libtonc/lib -ltonc -lm

# Rule Definitions
.PHONY: all clean

all: $(TARGET).gba

$(TARGET).gba: $(TARGET).elf
	@echo "Creating ROM: $@"
	$(OBJCOPY) -O binary $< $@
	@if [ -f "$(GBAFIX)" ]; then \
		$(GBAFIX) $@; \
	elif command -v gbafix >/dev/null 2>&1; then \
		gbafix $@; \
	else \
		echo "Warning: gbafix not found; skipping ROM header checksum validation."; \
	fi

$(TARGET).elf: $(OBJS)
	@echo "Linking ELF: $@"
	$(CC) $^ $(LDFLAGS) -o $@

main.o stadium.o: stadium.h
main.o link.o: link.h
main.o achievements.o: achievements.h
engine3d.o: ball_sprite.inc
models.o: car_models.inc models.h engine3d.h
main.o engine3d.o render.o stadium.o: engine3d.h render.h models.h

%.o: %.c
	@echo "Compiling C: $<"
	$(CC) $(CFLAGS) -c $< -o $@

clean:
	@echo "Cleaning project binaries..."
	rm -f $(OBJS) $(TARGET).elf $(TARGET).gba
