#ifndef __LCD_DRIVER_H
#define __LCD_DRIVER_H

#include "DEV_Config.h"

#define LCD_WIDTH   240
#define LCD_HEIGHT  280

#define LCD_SetBacklight(Value) DEV_Set_BL(DEV_BL_PIN, Value)

void LCD_Init(uint8_t isLandscape);
void LCD_SetCursor(UWORD Xstart, UWORD Ystart, UWORD Xend, UWORD Yend);
void LCD_Clear(UWORD Color);
void LCD_WriteData_Byte(UBYTE da);
void LCD_WriteData_Word(UWORD da);
void LCD_WriteReg(UBYTE da);

#endif
