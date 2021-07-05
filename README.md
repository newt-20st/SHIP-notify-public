# SHIP-notify
## 概要
[SHIP](https://ship.sakae-higashi.jp/)に新しいファイルが投稿された際に通知するシステム。

PaaSとしてHerokuを使用。Discord.pyの<code>@tasks.loop</code>で600秒毎に現在時間を確認し、予め設定していた時間であればSHIPやその他このシステムで更新を取得しているプラットフォームへAPIリクエストやスクレイピングを行い、データベースと差があれば更新し各媒体での通知を行う。

SHIPのスクレイピングにはseleniumを使用。中高それぞれの「連絡事項」「学習教材」「学校通信」のページを1日2～5回程度取得している。データベースに保存されていないものが見つかればそのリンクをクリックし、説明文やファイルのダウンロード＆SHIP-notify側のデータベースへのアップロードを行う。

データベースはFirebaseのFirestoreとStrageを使用。ファイルの保存に関しては無料枠の容量で抑えるため中学のページのものは保存を行っていない。

## 再利用にあたって
再利用(フォーク)などは基本自由としますが、一度連絡を入れてください。

### webDriver バージョン設定
環境変数 <code>CHROMEDRIVER_VERSION</code> に[ここ](https://chromedriver.chromium.org/downloads)に記載されているバージョンをセットする。