const puppeteer = require('puppeteer-core');
const path = require('path');

(async () => {
  const htmlPath = path.resolve(__dirname, 'presentation.html');
  const pdfPath  = path.resolve(__dirname, 'presentation.pdf');

  const browser = await puppeteer.launch({
    executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-web-security'],
  });

  const page = await browser.newPage();

  // 1280×720 기준 — 18슬라이드
  await page.setViewport({ width: 1280, height: 720 });
  await page.goto('file:///' + htmlPath.replace(/\\/g, '/'), { waitUntil: 'networkidle2', timeout: 30000 });

  // 폰트 로드 대기
  await page.evaluate(() => document.fonts.ready);

  await page.pdf({
    path: pdfPath,
    width:  '1280px',
    height: '720px',
    printBackground: true,
    pageRanges: '',
  });

  await browser.close();
  console.log('PDF 생성 완료:', pdfPath);
})();
