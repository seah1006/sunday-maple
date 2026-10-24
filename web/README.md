# 썬데이 메이플 예보

Vite + React + TypeScript 정적 사이트입니다. 저장소 루트의 `data/site/*.json`을 읽습니다.

```powershell
npm install
npm run dev
npm run lint
npm run test -- --run
npm run build
npm run preview
```

`predev`와 `prebuild`가 데이터를 `public/data`로 복사합니다. 복사본·node_modules·dist는 추적하지 않습니다. 라우팅은 HashRouter, Vite base는 `./`입니다. 배포 설정은 이번 범위가 아닙니다.
