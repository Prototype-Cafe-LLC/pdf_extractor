# PDF RAG HTTPサーバー ドキュメント

このドキュメントでは、PDF RAG HTTPサーバーのAPIエンドポイント、認証、デプロイ、
使用例について包括的に説明します。

**重要**: このHTTPサーバーは、Claude DesktopやCursorなどのMCPクライアント用では
ありません。MCPクライアントはHTTPではなくstdioトランスポートを使用します。
このサーバーは以下の用途に使用してください：

- Webアプリケーション
- チームコラボレーション
- リモートAPIアクセス
- サービス間通信

MCPクライアント統合については、メインのREADME.mdを参照し、
`src.mcp.simple_server`を使用してください。

## 目次

- [概要](#概要)
- [クイックスタート](#クイックスタート)
- [認証](#認証)
- [APIエンドポイント](#apiエンドポイント)
- [Python クライアントSDK](#python-クライアントsdk)
- [設定](#設定)
- [デプロイ](#デプロイ)
- [セキュリティのベストプラクティス](#セキュリティのベストプラクティス)
- [トラブルシューティング](#トラブルシューティング)

## 概要

PDF RAG HTTPサーバーは、PDF RAGシステムのRESTful APIインターフェースを提供し、
以下を可能にします：

- 認証を使用したマルチユーザーアクセス
- RAG機能へのリモートアクセス
- Webアプリケーションとの簡単な統合
- スケーラブルなデプロイオプション
- レート制限とセキュリティ機能

## クイックスタート

### インストール

```bash
# 依存関係のインストール
uv pip install -r pyproject.toml

# または、HTTPサーバーの追加機能付きでインストール
uv pip install -e ".[http]"
```

### サーバーの起動

```bash
# HTTPサーバーを起動
python -m src.mcp.http_server

# またはカスタム設定で起動
HTTP_SERVER_PORT=8080 python -m src.mcp.http_server

# 複数ワーカーでの本番デプロイ
uvicorn src.mcp.http_server:app --host 0.0.0.0 --port 8000 --workers 4
```

### サーバーのテスト

```bash
# ヘルスチェック
curl http://localhost:8000/api/health

# ログインしてJWTトークンを取得
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

## 認証

サーバーは2つの認証方法をサポートしています：

### 1. JWT認証

インタラクティブユーザーとWebアプリケーション用：

```bash
# ログインしてJWTトークンを取得
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# リクエストでトークンを使用
curl http://localhost:8000/api/documents \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 2. APIキー認証

サービス間通信用：

```bash
# ヘッダーでAPIキーを使用
curl http://localhost:8000/api/documents \
  -H "X-API-Key: demo-api-key-12345"
```

### 認証情報の設定

**⚠️ 重要: セキュリティ上の理由から、デフォルトの認証情報は提供されていません！**

環境変数を使用して認証情報を設定する必要があります：

#### 必須設定

```bash
# 必須: トークン署名用のJWTシークレットキー
export JWT_SECRET_KEY="your-secret-key-here"
```

#### オプションの認証方法

ニーズに基づいて、1つまたは両方の認証方法を選択してください：

##### オプション1: ユーザー名/パスワード認証

最適な用途：Webアプリケーション、管理ダッシュボード、インタラクティブな使用

```bash
# 管理者ユーザー名を設定
export ADMIN_USERNAME="admin"

# パスワードハッシュを生成（パスワードの入力を求められます）
python scripts/generate_password_hash.py

# 生成されたハッシュをエクスポート
export ADMIN_PASSWORD_HASH="$2b$12$..."  # スクリプト出力からコピー
```

##### オプション2: APIキー認証

最適な用途：自動化スクリプト、CI/CDパイプライン、サービス間通信

```bash
# APIキーを設定（形式: api_key:service_name:rate_limit_per_hour）
# - api_key: 実際のAPIキー文字列
# - service_name: サービスの説明的な名前
# - rate_limit_per_hour: 1時間あたりの許可リクエスト数
export API_KEYS="key1:service1:1000,key2:service2:5000"

# 実際の例：
# export API_KEYS="sk-prod-abc123:production-web:10000,sk-dev-xyz789:development:1000"
# export API_KEYS="secure-key-mobile:mobile-app:5000,secure-key-analytics:analytics-service:2000"
```

**注意**:

- 認証方法が設定されていない場合、すべてのAPIエンドポイント（/api/healthを除く）
  は401 Unauthorizedを返します
- 最大の柔軟性のために、両方の方法を同時に有効にできます
- サーバーは最初にJWT認証をチェックし、次にAPIキー認証にフォールバックします

## APIエンドポイント

### 認証エンドポイント

#### POST /api/auth/login

ユーザー名とパスワードでログイン。

**リクエスト:**

```json
{
  "username": "admin",
  "password": "admin123"
}
```

**レスポンス:**

```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

#### GET /api/auth/me

現在のユーザー情報を取得。

**ヘッダー:** Authorization: Bearer TOKEN

**レスポンス:**

```json
{
  "username": "admin",
  "is_active": true,
  "is_admin": true
}
```

### ドキュメント管理エンドポイント

#### POST /api/query

技術文書をクエリ。

**リクエスト:**

```json
{
  "question": "RAGシステムの設定方法は？",
  "top_k": 5
}
```

**レスポンス:**

```json
{
  "answer": "RAGシステムを設定するには...",
  "sources": [
    {
      "document": "configuration.pdf",
      "page": 12,
      "section": "Configuration"
    }
  ],
  "confidence": 0.95,
  "processing_time": 1.23
}
```

#### POST /api/documents

単一のPDFドキュメントを追加。

**リクエスト:**

```json
{
  "pdf_path": "/path/to/document.pdf",
  "document_type": "manual"
}
```

**レスポンス:**

```json
{
  "message": "Successfully added document: document.pdf",
  "success": true
}
```

#### POST /api/documents/batch

フォルダから複数のPDFドキュメントを追加。

**リクエスト:**

```json
{
  "folder_path": "/path/to/pdf/folder",
  "document_type": "documentation",
  "recursive": true
}
```

**レスポンス:**

```json
{
  "message": "Processed 10 files. Successfully added: 9, Failed: 1",
  "success": false
}
```

#### POST /api/documents/upload

PDFドキュメントを直接アップロード。

**リクエスト:** ファイル付きマルチパートフォームデータ

```bash
curl -X POST http://localhost:8000/api/documents/upload \
  -H "Authorization: Bearer TOKEN" \
  -F "file=@document.pdf" \
  -F "document_type=manual"
```

**レスポンス:**

```json
{
  "message": "Successfully added document: document.pdf",
  "success": true
}
```

#### GET /api/documents

ナレッジベース内のすべてのドキュメントをリスト。

**レスポンス:**

```json
{
  "documents": [
    {
      "document": "manual.pdf",
      "type": "manual",
      "chunk_count": 42,
      "source": "/docs/manual.pdf"
    }
  ],
  "total_count": 1
}
```

### システム管理エンドポイント

#### GET /api/system/info

システム情報とコンポーネントステータスを取得。

**レスポンス:**

```json
{
  "server_version": "1.0.0",
  "components_status": {
    "vector_store": true,
    "embedding_model": true,
    "llm_model": true
  },
  "configuration": {
    "llm_type": "openai",
    "llm_model": "gpt-4",
    "embedding_model": "all-MiniLM-L6-v2",
    "collection_name": "technical_docs"
  },
  "features": [
    "RAGを使用した技術文書のクエリ",
    "PDFドキュメントをナレッジベースに追加",
    "API経由でPDFファイルをアップロード",
    "システム内のすべてのドキュメントをリスト",
    "システムステータスと設定を取得",
    "JWTベースの認証",
    "WebクライアントのCORSサポート"
  ]
}
```

#### DELETE /api/database

ベクターデータベースをクリア。

**リクエスト:**

```json
{
  "confirm": true
}
```

**レスポンス:**

```json
{
  "message": "Successfully cleared database. Removed 10 documents (420 chunks).",
  "success": true
}
```

#### GET /api/health

ヘルスチェックエンドポイント（認証不要）。

**レスポンス:**

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "components": {
    "rag_engine": true,
    "configuration": true
  }
}
```

## Python クライアントSDK

### SDKのインストール

クライアントSDKはメインパッケージに含まれています：

```python
from src.mcp.http_client import PDFRAGClient
```

### 基本的な使用方法

```python
# APIキーを使用
client = PDFRAGClient(
    base_url="http://localhost:8000",
    api_key="your-api-key"
)

# ユーザー名/パスワードを使用
client = PDFRAGClient(
    base_url="http://localhost:8000",
    username="admin",
    password="admin123"
)

# ドキュメントをクエリ
result = client.query("システムはどのように動作しますか？")
print(f"回答: {result['answer']}")
print(f"信頼度: {result['confidence']}")

# ドキュメントを追加
response = client.add_document("/path/to/doc.pdf", "manual")
print(response['message'])

# ドキュメントをリスト
docs = client.list_documents()
for doc in docs:
    print(f"- {doc['document']} ({doc['chunk_count']} チャンク)")
```

### コンテキストマネージャー

```python
with PDFRAGClient(api_key="your-api-key") as client:
    # クライアントセッションは自動的に管理されます
    health = client.health_check()
    print(f"サーバーステータス: {health['status']}")
```

### エラーハンドリング

```python
try:
    client.add_document("/path/to/doc.pdf")
except FileNotFoundError:
    print("PDFファイルが見つかりません")
except requests.HTTPError as e:
    if e.response.status_code == 401:
        print("認証に失敗しました")
    elif e.response.status_code == 429:
        print("レート制限を超過しました")
```

## 設定

### 環境変数

```bash
# サーバー設定
HTTP_SERVER_HOST=0.0.0.0
HTTP_SERVER_PORT=8000

# 認証
JWT_SECRET_KEY=your-secret-key-here
DEFAULT_API_KEY=your-api-key-here

# LLM設定
LLM_TYPE=openai
LLM_MODEL=gpt-4
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

### 設定ファイル

`config/http_server_config.yaml`を編集：

```yaml
http_server:
  host: "0.0.0.0"
  port: 8000
  workers: 4
  cors_origins:
    - "https://yourdomain.com"

auth:
  jwt_algorithm: "HS256"
  access_token_expire_minutes: 1440

rate_limits:
  default: 100
  authenticated: 1000
  api_key: 5000
```

## デプロイ

### Dockerデプロイ

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY . .

RUN pip install -e .

EXPOSE 8000

CMD ["uvicorn", "src.mcp.http_server:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  pdf-rag-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - LLM_TYPE=openai
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./certs:/etc/nginx/certs
    depends_on:
      - pdf-rag-api
```

### 本番環境へのデプロイ

1. **HTTPSを使用**: 本番環境では常にTLS/SSLを使用
2. **デフォルトの認証情報を変更**: すべてのデフォルトパスワードとAPIキーを更新
3. **安全なJWTシークレットを設定**: 強力でランダムなシークレットキーを使用
4. **レート制限を設定**: ニーズに基づいて制限を調整
5. **モニタリングを有効化**: メトリクスエンドポイントを使用してモニタリング
6. **ロギングを設定**: 適切なログローテーションとモニタリングを設定

### Nginx設定

```nginx
server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate /etc/nginx/certs/cert.pem;
    ssl_certificate_key /etc/nginx/certs/key.pem;

    location / {
        proxy_pass http://pdf-rag-api:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## セキュリティのベストプラクティス

### 認証と認可

1. **デフォルトの認証情報を即座に変更**
2. **強力なパスワードとAPIキーを使用**
3. **JWTシークレットを定期的にローテーション**
4. **適切なユーザーロールと権限を実装**
5. **すべての通信にHTTPSを使用**

### 入力検証

1. **ファイルサイズ制限が適用されています（デフォルト50MB）**
2. **パストラバーサル保護が実装されています**
3. **すべてのユーザー入力の入力サニタイゼーション**
4. **レート制限により悪用を防止**

### セキュリティヘッダー（予定）

**注意**: セキュリティヘッダーは`config/http_server_config.yaml`で設定されていますが、
まだサーバーによって自動的に適用されません。本番環境でのデプロイでは、
リバースプロキシ（nginx/Apache）またはロードバランサーでこれらのヘッダーを設定してください：

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security: max-age=31536000`

### APIキー管理

1. **強力なAPIキーを生成**: 暗号学的に安全なランダムジェネレーターを使用
2. **キーを安全に保存**: バージョン管理にキーをコミットしない
3. **キーを定期的にローテーション**: キーローテーションポリシーを実装
4. **キーの使用を監視**: APIキーの使用を追跡および監査

#### APIキーフォーマットの詳細

`API_KEYS`環境変数を設定する際は、以下の形式を使用してください：

```bash
# 形式: api_key:service_name:rate_limit_per_hour
export API_KEYS="key1:name1:limit1,key2:name2:limit2,..."
```

**コンポーネント:**

- **api_key**: 実際のAPIキー文字列（例："sk-1234567890abcdef"）
  - セキュリティのため、少なくとも32文字以上にする必要があります
  - 英数字とハイフンのみを使用
  - 安全なランダムメソッドを使用して生成

- **service_name**: サービスの説明的な識別子
  （例："web-app"、"mobile-ios"、"analytics"）
  - ロギングとモニタリングに使用
  - APIキーごとに一意である必要があります
  - どのサービスがリクエストを行っているかを識別するのに役立ちます

- **rate_limit_per_hour**: 1時間あたりの最大リクエスト数
  （例：1000、5000、10000）
  - APIキーごとに適用
  - 悪用を防ぎ、公平な使用を保証
  - 予想されるサービス負荷に基づいて設定

**設定例:**

```bash
# 開発環境
export API_KEYS="dev-key-123:local-testing:1000"

# 複数サービスを持つ本番環境（読みやすさのため分割）
export API_KEYS="sk-prod-web-abc123:production-website:10000,\
sk-prod-mobile-xyz789:mobile-app:5000,\
sk-prod-analytics-qrs456:analytics-service:2000"

# 混合環境
export API_KEYS="prod-key-1:web-frontend:10000,\
staging-key-1:staging-api:5000,\
test-key-1:integration-tests:1000"
```

## トラブルシューティング

### よくある問題

#### サーバーが起動しない

```bash
# ポートが既に使用されているか確認
lsof -i :8000

# 別のポートを使用
HTTP_SERVER_PORT=8080 python -m src.mcp.http_server
```

#### 認証が失敗する

```bash
# JWTシークレットが設定されているか確認
echo $JWT_SECRET_KEY

# ログでユーザー認証情報を確認
tail -f logs/http_server.log
```

#### レート制限エラー

```python
# 特定のAPIキーのレート制限を増やす
# config/http_server_config.yamlを編集
rate_limits:
  api_key: 10000  # 制限を増やす
```

#### ファイルアップロードが失敗する

```bash
# ファイルサイズを確認
ls -lh document.pdf

# ファイルが有効なPDFか確認
file document.pdf
```

### デバッグモード

デバッグロギングを有効化：

```bash
# ログレベルをDEBUGに設定
export LOG_LEVEL=DEBUG
python -m src.mcp.http_server
```

### パフォーマンスチューニング

1. **ワーカーを増やす**: 本番環境では複数のワーカーを使用
2. **キャッシングを有効化**: 頻繁なクエリのためにRedisを実装
3. **データベース最適化**: ベクターデータベースが適切にインデックスされていることを確認
4. **ロードバランシング**: ロードバランサーの背後で複数のサーバーインスタンスを使用

## APIクライアントの例

### cURLの例

```bash
# APIキーでクエリ
curl -X POST http://localhost:8000/api/query \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"question": "RAGとは何ですか？"}'

# JWTでファイルをアップロード
curl -X POST http://localhost:8000/api/documents/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@document.pdf" \
  -F "document_type=manual"
```

### JavaScript/TypeScript

```typescript
// Fetch APIを使用
const response = await fetch('http://localhost:8000/api/query', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': 'your-api-key'
  },
  body: JSON.stringify({
    question: 'どのように動作しますか？',
    top_k: 5
  })
});

const data = await response.json();
console.log(data.answer);
```

### Python Requests

```python
import requests

# シンプルなクエリ
response = requests.post(
    'http://localhost:8000/api/query',
    json={'question': '設定は何ですか？'},
    headers={'X-API-Key': 'your-api-key'}
)

print(response.json()['answer'])
```

## モニタリングとメトリクス

### ヘルスチェック

```bash
# Kubernetes livenessプローブ
curl -f http://localhost:8000/api/health || exit 1
```

### Prometheusメトリクス（予定）

**注意**: Prometheusメトリクスエンドポイントは計画されていますが、
まだ実装されていません。この機能は本番環境のモニタリング機能のロードマップにあります。

### ロギング

ログは以下に書き込まれます：

- コンソール（stdout）
- ファイル：`logs/http_server.log`
- 設定可能なサイズと保持期間でログをローテーション

## MCPサーバーからの移行

既存のMCP stdioサーバーから移行するには：

1. **両方のサーバーを実行し続ける**: HTTPサーバーは追加のインターフェースです
2. **クライアントコードを更新**: MCPクライアントをHTTPクライアントに置き換え
3. **認証を移行**: ユーザーとAPIキーを設定
4. **徹底的にテスト**: すべての機能が正しく動作することを確認
5. **段階的なロールアウト**: サービスを一度に1つずつ移行

## サポートと貢献

問題、機能リクエスト、または貢献については：

1. [GitHubリポジトリ](https://github.com/your-org/pdf-rag-system)を確認
2. 新しい問題を作成する前に既存の問題を確認
3. 貢献ガイドラインに従う
4. テスト付きでプルリクエストを提出

## ライセンス

このプロジェクトは、LICENSEファイルに指定されている条件でライセンスされています。
