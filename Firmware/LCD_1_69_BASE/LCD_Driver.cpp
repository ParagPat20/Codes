#include "LCD_Driver.h"

static uint8_t g_isLandscape = 0;

static void LCD_Reset(void)
{
    DEV_Digital_Write(DEV_CS_PIN, 0);
    DEV_Delay_ms(20);
    DEV_Digital_Write(DEV_RST_PIN, 0);
    DEV_Delay_ms(20);
    DEV_Digital_Write(DEV_RST_PIN, 1);
    DEV_Delay_ms(20);
}

void LCD_WriteData_Byte(UBYTE da) 
{ 
    DEV_Digital_Write(DEV_CS_PIN, 0);
    DEV_Digital_Write(DEV_DC_PIN, 1);
    DEV_SPI_WRITE(da);  
    DEV_Digital_Write(DEV_CS_PIN, 1);
}  

void LCD_WriteData_Word(UWORD da)
{
    UBYTE i = (da >> 8) & 0xff;
    DEV_Digital_Write(DEV_CS_PIN, 0);
    DEV_Digital_Write(DEV_DC_PIN, 1);
    DEV_SPI_WRITE(i);
    DEV_SPI_WRITE(da);
    DEV_Digital_Write(DEV_CS_PIN, 1);
}   

void LCD_WriteReg(UBYTE da)  
{ 
    DEV_Digital_Write(DEV_CS_PIN, 0);
    DEV_Digital_Write(DEV_DC_PIN, 0);
    DEV_SPI_WRITE(da);
    DEV_Digital_Write(DEV_CS_PIN, 1);
}

void LCD_Init(uint8_t isLandscape)
{
    g_isLandscape = isLandscape;
    LCD_Reset();

    // Memory Data Access Control (MADCTL) - Orientation
    LCD_WriteReg(0x36);
    if (isLandscape) {
        LCD_WriteData_Byte(0x70); // Landscape
    } else {
        LCD_WriteData_Byte(0x00); // Portrait
    }

    LCD_WriteReg(0x3A);
    LCD_WriteData_Byte(0x05); // 16-bit/pixel RGB565

    LCD_WriteReg(0xB2);
    LCD_WriteData_Byte(0x0B);
    LCD_WriteData_Byte(0x0B);
    LCD_WriteData_Byte(0x00);
    LCD_WriteData_Byte(0x33);
    LCD_WriteData_Byte(0x33);

    LCD_WriteReg(0xB7);
    LCD_WriteData_Byte(0x11);

    LCD_WriteReg(0xBB);
    LCD_WriteData_Byte(0x35);

    LCD_WriteReg(0xC0);
    LCD_WriteData_Byte(0x2C);

    LCD_WriteReg(0xC2);
    LCD_WriteData_Byte(0x01);

    LCD_WriteReg(0xC3);
    LCD_WriteData_Byte(0x0D);

    LCD_WriteReg(0xC4);
    LCD_WriteData_Byte(0x20);

    LCD_WriteReg(0xC6);
    LCD_WriteData_Byte(0x13);

    LCD_WriteReg(0xD0);
    LCD_WriteData_Byte(0xA4);
    LCD_WriteData_Byte(0xA1);

    LCD_WriteReg(0xD6);
    LCD_WriteData_Byte(0xA1);

    LCD_WriteReg(0xE0);
    LCD_WriteData_Byte(0xF0);
    LCD_WriteData_Byte(0x06);
    LCD_WriteData_Byte(0x0B);
    LCD_WriteData_Byte(0x0A);
    LCD_WriteData_Byte(0x09);
    LCD_WriteData_Byte(0x26);
    LCD_WriteData_Byte(0x29);
    LCD_WriteData_Byte(0x33);
    LCD_WriteData_Byte(0x41);
    LCD_WriteData_Byte(0x18);
    LCD_WriteData_Byte(0x16);
    LCD_WriteData_Byte(0x15);
    LCD_WriteData_Byte(0x29);
    LCD_WriteData_Byte(0x2D);

    LCD_WriteReg(0xE1);
    LCD_WriteData_Byte(0xF0);
    LCD_WriteData_Byte(0x04);
    LCD_WriteData_Byte(0x08);
    LCD_WriteData_Byte(0x08);
    LCD_WriteData_Byte(0x07);
    LCD_WriteData_Byte(0x03);
    LCD_WriteData_Byte(0x28);
    LCD_WriteData_Byte(0x32);
    LCD_WriteData_Byte(0x40);
    LCD_WriteData_Byte(0x3B);
    LCD_WriteData_Byte(0x19);
    LCD_WriteData_Byte(0x18);
    LCD_WriteData_Byte(0x2A);
    LCD_WriteData_Byte(0x2E);

    LCD_WriteReg(0xE4);
    LCD_WriteData_Byte(0x25);
    LCD_WriteData_Byte(0x00);
    LCD_WriteData_Byte(0x00);

    LCD_WriteReg(0x21); // Display Inversion ON (IPS Panel)

    LCD_WriteReg(0x11); // Sleep Out
    DEV_Delay_ms(120);
    LCD_WriteReg(0x29); // Display ON
}

void LCD_SetCursor(UWORD Xstart, UWORD Ystart, UWORD Xend, UWORD Yend)
{ 
    if (g_isLandscape) {
        // Landscape: X has offset +20 (20 to 299), Y is 0 to 239
        LCD_WriteReg(0x2A);
        LCD_WriteData_Byte((Xstart + 20) >> 8);
        LCD_WriteData_Byte(Xstart + 20);
        LCD_WriteData_Byte((Xend + 20) >> 8);
        LCD_WriteData_Byte(Xend + 20);
        
        LCD_WriteReg(0x2B);
        LCD_WriteData_Byte(Ystart >> 8);
        LCD_WriteData_Byte(Ystart);
        LCD_WriteData_Byte(Yend >> 8);
        LCD_WriteData_Byte(Yend);
    } else {
        // Portrait: X is 0 to 239, Y has offset +20 (20 to 299)
        LCD_WriteReg(0x2A);
        LCD_WriteData_Byte(Xstart >> 8);
        LCD_WriteData_Byte(Xstart);
        LCD_WriteData_Byte(Xend >> 8);
        LCD_WriteData_Byte(Xend);

        LCD_WriteReg(0x2B);
        LCD_WriteData_Byte((Ystart + 20) >> 8);
        LCD_WriteData_Byte(Ystart + 20);
        LCD_WriteData_Byte((Yend + 20) >> 8);
        LCD_WriteData_Byte(Yend + 20);
    }

    LCD_WriteReg(0X2C); // Memory Write
}

void LCD_Clear(UWORD Color)
{
    UWORD width  = g_isLandscape ? 280 : 240;
    UWORD height = g_isLandscape ? 240 : 280;

    LCD_SetCursor(0, 0, width - 1, height - 1);
    DEV_Digital_Write(DEV_DC_PIN, 1);
    DEV_Digital_Write(DEV_CS_PIN, 0);
    for (int i = 0; i < width * height; i++) {
        DEV_SPI_WRITE((Color >> 8) & 0xFF);
        DEV_SPI_WRITE(Color & 0xFF);
    }
    DEV_Digital_Write(DEV_CS_PIN, 1);
}
