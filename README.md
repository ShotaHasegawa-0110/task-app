# タスク管理アプリ — Podman で起動する手順

## 1. ビルド

```bash
cd task-app
podman build -t task-app .
```

## 2. 起動

```bash
podman run -p 5000:5000 task-app
```

## 3. ブラウザでアクセス

http://localhost:5000

ログイン画面が表示されるので「新規ユーザ登録」からアカウントを作成してください。

## 4. 停止

```bash
podman stop $(podman ps -q --filter ancestor=task-app)
```
