#include <tonc.h>
int main() { REG_TM2D = 0; REG_TM2CNT = TM_FREQ_1024 | TM_ENABLE; REG_TM3D = 0; REG_TM3CNT = TM_CASCADE | TM_ENABLE; return 0; }
