const BAD_SCENARIO_URL_ERROR = 'bad scenario URL';

export default class BitReader {
  private readonly byteList: Uint8Array;
  private currentByte = 0;
  private nextByte = 0;
  private nextBit = 8;

  constructor(encodedBytes: string) {
    let bytes = encodedBytes;

    bytes += '='.repeat((4 - (bytes.length % 4)) % 4);
    bytes = bytes.replace(/-/g, '+');
    bytes = bytes.replace(/_/g, '/');

    try {
      bytes = atob(bytes);
    }
    catch {
      throw BAD_SCENARIO_URL_ERROR;
    }

    this.byteList = new Uint8Array(
      bytes.split('').map((char) => char.charCodeAt(0)),
    );
  }

  readBits(numBits: number): number {
    let value = 0;
    let bitsRead = 0;

    while (true) {
      if (this.nextBit === 8) {
        if (this.nextByte === this.byteList.length) {
          throw BAD_SCENARIO_URL_ERROR;
        }
        this.currentByte = this.byteList[this.nextByte++] ?? 0;
        this.nextBit = 0;
      }

      const bitsToRead = Math.min(8 - this.nextBit, numBits);
      const mask = ((1 << bitsToRead) - 1) << this.nextBit;
      value += ((this.currentByte & mask) >> this.nextBit) << bitsRead;
      this.nextBit += bitsToRead;
      numBits -= bitsToRead;

      if (numBits === 0) {
        return value;
      }

      bitsRead += bitsToRead;
    }
  }
}
