# Web Future

RubiMorph は Web 専用ツールではありません。将来 Web 版を作る場合も、ローカル CLI / GUI と同じ core 仕様を共有します。

## 方針

- core と UI を分離したままにする。
- Web 版が本文を外部送信するかどうかを明示する。
- ローカル実行版を主軸に残す。
- platform profile、parser、renderer、diagnostics の仕様を再利用する。

## 候補

- Python core をローカルサーバーとして動かす。
- 中間トークン仕様を TypeScript へ移植する。
- WASM などでローカル処理に寄せる。

## 未決定事項

- ホスティングするか。
- ログ保存を行うか。
- 原稿本文をサーバーに送る設計を許可するか。
- ブラウザ内処理で十分な性能を出せるか。
