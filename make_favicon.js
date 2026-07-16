// Generate favicon assets from the club logo using sharp.
// The logo has a pure-black background, so we fit it (contain) onto a black
// square — nothing gets cropped and the padding blends seamlessly.
const sharp = require('sharp');
const fs = require('fs');
const path = require('path');

const SRC = path.join(__dirname, 'assets/locations/39761872-4700-4c3f-aeaf-d4fed29685b4.JPG');
const BG = { r: 0, g: 0, b: 0 };

async function square(size, outName) {
  await sharp(SRC)
    .resize(size, size, { fit: 'contain', background: BG })
    .png()
    .toFile(path.join(__dirname, outName));
  console.log('wrote', outName, `(${size}x${size})`);
}

// Wrap a 32x32 PNG buffer into a valid .ico (ICO supports PNG-encoded entries).
async function makeIco() {
  const size = 32;
  const png = await sharp(SRC)
    .resize(size, size, { fit: 'contain', background: BG })
    .png()
    .toBuffer();

  const header = Buffer.alloc(6);
  header.writeUInt16LE(0, 0);   // reserved
  header.writeUInt16LE(1, 2);   // type: icon
  header.writeUInt16LE(1, 4);   // count: 1 image

  const entry = Buffer.alloc(16);
  entry.writeUInt8(size, 0);          // width
  entry.writeUInt8(size, 1);          // height
  entry.writeUInt8(0, 2);             // palette
  entry.writeUInt8(0, 3);             // reserved
  entry.writeUInt16LE(1, 4);          // color planes
  entry.writeUInt16LE(32, 6);         // bits per pixel
  entry.writeUInt32LE(png.length, 8); // size of PNG data
  entry.writeUInt32LE(6 + 16, 12);    // offset of PNG data

  fs.writeFileSync(path.join(__dirname, 'favicon.ico'), Buffer.concat([header, entry, png]));
  console.log('wrote favicon.ico (32x32)');
}

(async () => {
  await square(180, 'apple-touch-icon.png');
  await square(32, 'favicon-32x32.png');
  await square(16, 'favicon-16x16.png');
  await makeIco();
})();
