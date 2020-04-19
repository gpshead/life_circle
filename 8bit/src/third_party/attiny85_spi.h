#ifndef _ATTINY85_SPI_H_
#define _ATTINY85_SPI_H_

#include <stdint.h>

void hw_spi_init(void);
void hw_spi_end(void);
void spi_out(const uint8_t);

#endif  // _ATTINY86_SPI_H_