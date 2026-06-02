const puppeteer = require('puppeteer-core');
const path = require('path');

(async () => {
  const htmlPath = path.resolve(__dirname, 'bible.html');
  const pdfPath  = path.resolve(__dirname, 'bible_new.pdf');

  const browser = await puppeteer.launch({
    executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-web-security'],
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1280, height: 720 });
  await page.goto('file:///' + htmlPath.replace(/\\/g, '/'), { waitUntil: 'networkidle2', timeout: 30000 });
  await page.evaluate(() => document.fonts.ready);

  // 전체 슬라이드 수 파악
  const total = await page.evaluate(() => document.querySelectorAll('.slide').length);
  console.log('총 슬라이드:', total);

  const buffers = [];

  for (let i = 0; i < total; i++) {
    // 해당 슬라이드로 이동
    await page.evaluate((idx) => {
      const slides = Array.from(document.querySelectorAll('.slide'));
      slides.forEach(s => s.classList.remove('active'));
      slides[idx].classList.add('active');
    }, i);

    // 렌더링 안정화 대기
    await new Promise(r => setTimeout(r, 80));

    const buf = await page.screenshot({ type: 'png', clip: { x: 0, y: 0, width: 1280, height: 720 } });
    buffers.push(buf);
    process.stdout.write(`\r슬라이드 ${i + 1}/${total} 캡처 완료`);
  }

  console.log('\n스크린샷 완료, PDF 합치는 중...');

  // 스크린샷을 PDF로 합치기
  const pdfPage = await browser.newPage();
  await pdfPage.setViewport({ width: 1280, height: 720 });

  // 모든 이미지를 하나의 HTML에 넣어 PDF 생성
  const imgs = buffers.map(buf => buf.toString('base64'));
  const html = `<!DOCTYPE html><html><head><style>
    * { margin:0; padding:0; box-sizing:border-box; }
    body { background: #000; }
    .page { width:1280px; height:720px; page-break-after:always; overflow:hidden; }
    .page:last-child { page-break-after:auto; }
    img { width:1280px; height:720px; display:block; }
  </style></head><body>
    ${imgs.map(b => `<div class="page"><img src="data:image/png;base64,${b}"></div>`).join('')}
  </body></html>`;

  await pdfPage.setContent(html, { waitUntil: 'networkidle0' });
  await pdfPage.pdf({
    path: pdfPath,
    width:  '1280px',
    height: '720px',
    printBackground: true,
    pageRanges: '',
  });

  await browser.close();
  console.log('PDF 생성 완료:', pdfPath);
})();
