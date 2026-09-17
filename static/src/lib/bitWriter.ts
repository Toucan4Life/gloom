const MAX_WRITABLE_BITS = 32;

export default class BitWriter {
  private readonly byteList: number[] = [];
  private scratchByte = 0;
  private nextBit = 0;

  result(): string {
    const bytes = btoa(String.fromCharCode(...this.byteList))
      .replace(/\+/g, '-')
      .replace(/\//g, '_')
      .replace(/=+$/, '');

    return bytes;
  }

  flush(): void {
    if (this.nextBit !== 0) {
      this.byteList.push(this.scratchByte);
      this.scratchByte = 0;
      this.nextBit = 0;
    }
  }

  writeBits(numBits: number, value: number): void {
    if (numBits > MAX_WRITABLE_BITS) {
      throw 'too many bits written';
    }
    if (value > (1 << numBits) - 1) {
      throw 'too few bits written';
    }
    if (value < 0) {
      throw 'writing negative number';
    }

    while (true) {
      if (this.nextBit + numBits < 8) {
        this.scratchByte |= value << this.nextBit;
        this.nextBit += numBits;
        return;
      }

      const bitsToWrite = 8 - this.nextBit;
      const mask = (1 << bitsToWrite) - 1;
      this.scratchByte |= (value & mask) << this.nextBit;

      this.byteList.push(this.scratchByte);
      this.scratchByte = 0;
      this.nextBit = 0;

      numBits -= bitsToWrite;
      value >>= bitsToWrite;
    }
  }
}
