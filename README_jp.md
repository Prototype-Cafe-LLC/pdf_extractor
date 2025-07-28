# PDF Extractor

PDFファイルをMarkdown形式に簡単に変換します。このコマンドラインツールは
`pymupdf4llm`を使用して、フォーマット、テーブル、構造を保持しながら
PDFからコンテンツを抽出します。

## 🚀 クイックスタート（5分でセットアップ）

お好みのセットアップを選択してください：

### オプションA：Claude Desktop用MCPサーバー

MCPサーバーを素早く稼働させたい忙しいユーザー向け：

#### 1. クローンとインストール（2分）

```bash
git clone git@github.com:Prototype-Cafe-LLC/pdf_extractor.git
cd pdf_extractor
./install.sh
```

以上です！インストールスクリプトがuvのインストールを含むすべてを処理します。

#### 2. MCPサーバーの設定（1分）

Claude Desktopの設定ファイルに追加：
`~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "pdf-rag": {
      "command": "/path/to/pdf_extractor/.venv/bin/python",
      "args": ["/path/to/pdf_extractor/src/mcp/simple_server.py"],
      "env": {
        "ANTHROPIC_API_KEY": "your-api-key"
        // オプションのオーバーライド（デフォルト値を表示）：
        // "LLM_TYPE": "anthropic",
        // "LLM_MODEL": "claude-3-5-sonnet-20241022",
        // "EMBEDDING_MODEL": "sentence-transformers/all-MiniLM-L6-v2"
      }
    }
  }
}
```

**注意**：`ANTHROPIC_API_KEY`のみが必須です。サーバーは他の設定に適切なデフォルトを使用します。
OpenAIの場合は、`OPENAI_API_KEY`を使用し、`LLM_TYPE`を"openai"に設定してください。

#### 3. 使用開始（1分）

Claude Desktopを再起動してチャットを開始：

- **PDF追加**：「/path/to/manual.pdfのPDFをナレッジベースに追加して」
- **フォルダ追加**：「/Users/me/Documents/manualsからすべてのPDFを追加して」
- **質問をする**：「マニュアルにはネットワーク設定について何と書いてありますか？」
- **ドキュメント一覧**：「ナレッジベースのすべてのドキュメントを表示して」

これで、AIでPDFドキュメントにクエリする準備ができました！

### オプションB：チームアクセス用HTTP APIサーバー

共有APIサーバーが必要なチーム向け：

#### 1. インストール（上記と同じ）

オプションAと同じインストール手順を使用します。

#### 2. HTTPサーバーの設定（2分）

##### 必須設定

```bash
# 必須：LLM APIキーを設定（いずれか1つを選択）
export ANTHROPIC_API_KEY="your-anthropic-key"  # Claude用
# または
export OPENAI_API_KEY="your-openai-key"  # GPT-4用

# 必須：認証用のJWTシークレット
export JWT_SECRET_KEY="$(openssl rand -base64 32)"
```

##### オプション認証設定

認証方法を1つまたは両方選択できます：

##### オプション1：ユーザー名/パスワード認証（オプション）

```bash
# 管理者ユーザー名を設定（オプション、WebUIログイン用）
export ADMIN_USERNAME="admin"

# パスワードハッシュを生成（パスワードの入力を求められます）
python scripts/generate_password_hash.py
# 生成されたハッシュをコピーしてエクスポート：
export ADMIN_PASSWORD_HASH="$2b$12$..."
```

##### オプション2：APIキー認証（オプション）

```bash
# サービス間認証用のAPIキーを設定（形式：key:name:rate_limit）
export API_KEYS="prod-key-1:production:5000,dev-key-1:development:1000"
```

**注意**：認証情報を設定しない場合、すべてのAPIエンドポイントは401 Unauthorizedを
返します。使用ケースに最適な認証方法を選択してください。

#### 3. サーバー起動（1分）

```bash
# HTTPサーバーを起動
python -m src.mcp.http_server

# サーバーはhttp://localhost:8000で実行中
# APIドキュメントはhttp://localhost:8000/docsで利用可能
```

#### 4. クイックテスト

```bash
# curlでテスト
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your-password"}'

# またはPythonクライアントを使用
python -c "
from src.mcp.http_client import PDFRAGClient
client = PDFRAGClient(username='admin', password='your-password')
print(client.health_check())
"
```

これで、HTTP APIサーバーがチーム使用の準備完了です！

## 機能

### PDF抽出

- 📄 単一のPDFファイルまたはディレクトリ全体を変換
- 🔄 バッチ処理サポート
- 📁 再帰的なディレクトリ探索
- 🌏 日本語テキストサポート
- 📊 テーブルとフォーマットを保持
- 🖼️ 画像を含むPDFの処理
- ⚡ 高速で効率的な変換
- 🛡️ 優雅なエラー処理
- ✨ markdownlintによる自動マークダウンフォーマット

### RAG + LLM機能（新機能！）

- 🤖 **インテリジェントクエリ**：技術文書について質問
- 🔍 **セマンティック検索**：エンベディングを使用して関連コンテンツを検索
- 📚 **ソース帰属**：すべての応答が特定のドキュメントセクションを引用
- 🎯 **幻覚防止**：LLMは取得したコンテキストのみを使用
- 📊 **信頼度スコアリング**：応答の信頼性を示す
- 🔧 **MCPサーバー**：Claude Desktopおよび他のクライアント用の標準化されたツール
- 🌐 **マルチLLMサポート**：OpenAI（GPT-4、GPT-4o）、Anthropic（Claude 4 Opus、
  Claude 3）、Ollama（O3、Llama 3.1）統合
- 📈 **ベクターデータベース**：ChromaDBによる永続的ストレージ
- 📝 **ローテーティングログ**：デバッグと監視用の自動ローテーション付きサーバーログ
- 🚀 **HTTP APIサーバー**：チームコラボレーション用のJWT/APIキー認証付きRESTful API
- 📦 **Python SDK**：HTTP APIとの簡単な統合のためのクライアントライブラリ

## インストール

### 前提条件

- Python 3.12以上
- [uv](https://github.com/astral.sh/uv)パッケージマネージャー
- [markdownlint-cli](https://github.com/igorshubovych/markdownlint-cli)
  （マークダウン検証に推奨）

### 基本セットアップ（PDF抽出のみ）

1. リポジトリをクローン：

   ```bash
   git clone git@github.com:Prototype-Cafe-LLC/pdf_extractor.git
   cd pdf_extractor
   ```

2. uvをインストール（まだインストールされていない場合）：

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. 仮想環境を作成し、依存関係をインストール：

   ```bash
   uv venv
   source .venv/bin/activate  # Windowsの場合：.venv\Scripts\activate
   uv pip install -e .
   ```

4. markdownlintをインストール（推奨）：

   ```bash
   npm install -g markdownlint-cli
   ```

### RAG + LLM MCPサーバーセットアップ

PDF ExtractorにはMCP（Model Context Protocol）サーバー統合による高度なRAG
（Retrieval Augmented Generation）機能が含まれています。これにより、
ソース帰属付きで技術文書をインテリジェントにクエリできます。

#### RAGの追加前提条件

- LLM APIキー（OpenAI、Anthropic、またはOllama）
- エンベディングモデルのダウンロード用インターネット接続（初回のみ）

#### セットアップガイド

詳細なセットアップ手順については、以下を参照してください：

- [Anthropicセットアップガイド](ANTHROPIC_SETUP.md) - Claudeモデル用
- [OpenAIセットアップガイド](OPENAI_SETUP.md) - GPTモデル用
- [Ollamaセットアップガイド](OLLAMA_SETUP.md) - ローカルモデル用
- [モデル比較](MODEL_COMPARISON.md) - Opus vs O3の詳細比較
- [プライバシーポリシー](PRIVACY_POLICY.md) - データ使用とプライバシーポリシー

#### RAGセットアップ手順

1. **APIキーを設定**（1つのプロバイダーを選択）：

   **オプションA：OpenAI**

   ```bash
   export OPENAI_API_KEY="your-openai-api-key-here"
   ```

   **オプションB：Anthropic**

   ```bash
   export ANTHROPIC_API_KEY="your-anthropic-api-key-here"
   ```

   **オプションC：Ollama（ローカル）**

   ```bash
   # APIキーは不要ですが、Ollamaがローカルで実行されていることを確認
   # https://ollama.ai/からOllamaをインストール
   ```

2. **RAG設定をカスタマイズ**（オプション）：

   `config/rag_config.yaml`を編集してカスタマイズ：
   - LLMプロバイダーとモデル
   - エンベディングモデル
   - チャンクサイズとオーバーラップ
   - ベクターデータベース設定

3. **RAGシステムをテスト**：

   ```bash
   python test_rag_basic.py
   ```

4. **MCPサーバーを設定して起動**：

   スタンドアロンテスト用：

   ```bash
   python src/mcp/simple_server.py
   ```

   MCPクライアント（Claude Desktop、Cursorなど）用に、MCP設定に追加：

   ```json
   {
     "mcpServers": {
       "pdf-rag-mcp": {
         "command": "/path/to/pdf_extractor/.venv/bin/python",
         "args": [
           "/path/to/pdf_extractor/src/mcp/simple_server.py"
         ],
         "env": {
           "FASTMCP_LOG_LEVEL": "ERROR",
           "ANTHROPIC_API_KEY": "your-api-key",
           "LLM_TYPE": "anthropic",
           "LLM_MODEL": "claude-3-opus-20240229",
           "EMBEDDING_MODEL": "sentence-transformers/all-MiniLM-L6-v2"
         }
       }
     }
   }
   ```

   **注意**：現在のMCPサーバーはstdio（標準入出力）トランスポートを使用します。
   HTTPベースのアクセスには、HTTP APIサーバーを使用してください（下記のHTTP APIサーバーセクションを参照）。

   **MCP設定のトラブルシューティング**：
   - "ModuleNotFoundError"が発生した場合、`-m`の代わりにargsで直接ファイルパスを使用
   - Pythonパスが仮想環境のPythonを指していることを確認
   - `cwd`パラメータはオプションですが、モジュール解決に役立ちます

#### 環境変数

MCPサーバーは環境変数による設定をサポートしており、YAMLファイルの設定を上書きします：

**必須APIキー（いずれか1つを選択）：**

```bash
# OpenAI用
export OPENAI_API_KEY="sk-your-openai-api-key"

# Anthropic用
export ANTHROPIC_API_KEY="sk-ant-your-anthropic-api-key"

# Ollama用（APIキー不要）
# Ollamaが実行されていることを確認：ollama serve
```

**オプションのモデル設定：**

```bash
# LLMプロバイダーをオーバーライド（anthropic、openai、ollama）
export LLM_TYPE="anthropic"

# LLMモデルをオーバーライド
export LLM_MODEL="claude-3-opus-20240229"

# エンベディングモデルをオーバーライド
export EMBEDDING_MODEL="sentence-transformers/all-MiniLM-L6-v2"
```

**ログ設定：**

```bash
# ログレベルを設定（DEBUG、INFO、WARNING、ERROR、CRITICAL）
export MCP_LOG_LEVEL="INFO"

# ログディレクトリをオーバーライド（デフォルト：./logs）
export MCP_LOG_DIR="/path/to/logs"

# ログローテーションサイズを設定（バイト単位、デフォルト：10MB）
export MCP_LOG_MAX_BYTES="10485760"

# 保持するバックアップファイル数を設定（デフォルト：5）
export MCP_LOG_BACKUP_COUNT="5"
```

**利用可能なモデル：**

- **Anthropic**：
  - Claude 3シリーズ：claude-3-opus-20240229、claude-3-sonnet-20240229、
    claude-3-haiku-20240307、claude-3-5-sonnet-20241022、claude-3-5-haiku-20241022
  - Claude 4シリーズ：claude-4-opus、claude-4-sonnet、claude-4-haiku（利用可能な場合）
- **OpenAI**：gpt-4、gpt-4-turbo、gpt-3.5-turbo、gpt-4o
- **Ollama**：llama2、llama3、mistral、codellama、o3（またはローカルにインストールされたモデル）

**注意**：APIキーはRAGシステムがインテリジェントな応答を生成するために使用されます。
基本的なPDF抽出機能はAPIキーなしで動作します。

**重要**：LLMは遅延初期化されます（クエリ作成時のみ）ので、ドキュメントの一覧表示や
PDF追加などの操作はAPIキーなしでも動作します。

### MCPサーバー vs HTTPサーバーの理解

このプロジェクトには2種類の異なるサーバーが含まれています：

1. **MCPサーバー**（`src.mcp.simple_server`）- Claude Desktop、CursorなどのAIアシスタント用
   - stdio（標準入出力）トランスポートを使用
   - AIツールとの直接統合
   - 認証不要（クライアントが処理）

2. **HTTP APIサーバー**（`src.mcp.http_server`）- WebアプリケーションとAPI用
   - HTTP/HTTPSトランスポートを使用
   - JWTとAPIキー認証
   - RESTful APIエンドポイント
   - チームコラボレーション機能

### HTTP APIサーバー（新機能！）

PDF RAGシステムにはチームコラボレーションとリモートアクセス用のRESTful HTTP APIサーバーが含まれています：

**機能**：

- 🔐 JWTとAPIキー認証
- 🌐 RESTful APIエンドポイント
- 🚀 非同期FastAPI実装
- 📦 Python クライアントSDK同梱
- 🛡️ パス検証による強化されたセキュリティ
- 📊 レート制限とCORSサポート

**クイックスタート**：

1. **環境変数を設定**：

   ```bash
   # 必須：トークン署名用のJWTシークレット
   export JWT_SECRET_KEY="your-secure-secret-key"
   
   # オプション：認証方法を選択
   # オプション1：ユーザー名/パスワード（WebUI/対話型使用向け）
   export ADMIN_USERNAME="admin"
   export ADMIN_PASSWORD_HASH="$(python scripts/generate_password_hash.py)"
   
   # オプション2：APIキー（自動化スクリプト/サービス向け）
   export API_KEYS="key1:service1:1000,key2:service2:5000"
   ```

2. **HTTPサーバーを起動**：

   ```bash
   python -m src.mcp.http_server
   # またはカスタム設定で
   uvicorn src.mcp.http_server:app --host 0.0.0.0 --port 8000 --workers 4
   ```

3. **Pythonクライアントを使用**：

   ```python
   from src.mcp.http_client import PDFRAGClient
   
   # APIキーを使用
   client = PDFRAGClient(api_key="your-api-key")
   
   # ドキュメントをクエリ
   result = client.query("システムはどのように動作しますか？")
   print(result['answer'])
   
   # ドキュメントを追加
   client.add_document("/path/to/document.pdf", "manual")
   ```

**APIエンドポイント**：

- `POST /api/auth/login` - JWTトークンを取得
- `GET /api/health` - ヘルスチェック
- `POST /api/query` - ドキュメントをクエリ
- `POST /api/documents` - 単一ドキュメントを追加
- `POST /api/documents/batch` - 複数ドキュメントを追加
- `GET /api/documents` - すべてのドキュメントを一覧表示
- `GET /api/system/info` - システム情報を取得
- `DELETE /api/database` - データベースをクリア

完全なドキュメントは[docs/HTTP_SERVER_README.md](docs/HTTP_SERVER_README.md)を参照してください。

## 使用方法

### 基本的なPDF抽出

単一のPDFファイルを変換：

```bash
python -m src.pdf_extractor document.pdf
# またはpip経由でインストールした場合：
pdf-extractor document.pdf
```

これにより、変換されたマークダウンファイルを含む`md`ディレクトリが作成されます。

### RAG + LLMクエリシステム

RAGシステムをセットアップした後、技術文書をインテリジェントにクエリできます：

#### Python APIを使用

```python
from rag_engine.retrieval import RAGEngine
import yaml

# 設定をロード
with open("config/rag_config.yaml", 'r') as f:
    config = yaml.safe_load(f)

# RAGエンジンを初期化
rag = RAGEngine(config)

# ナレッジベースにPDFドキュメントを追加
rag.add_pdf_document("path/to/document.pdf", "manual")

# ナレッジベースをクエリ
response = rag.query("ネットワーク設定をどのように設定しますか？")
print("回答:", response.answer)
print("ソース:", response.sources)
print("信頼度:", response.confidence)
```

#### MCPサーバーを使用

1. MCPサーバーを起動：

   ```bash
   python src/mcp/simple_server.py
   ```

2. Claude Desktopまたは他のMCPクライアントで、これらのツールを使用：

   - `pdfrag.query_technical_docs`：技術文書について質問
   - `pdfrag.add_document`：単一のPDFドキュメントをナレッジベースに追加
   - `pdfrag.add_documents`：フォルダから複数のPDFドキュメントを追加
   - `pdfrag.list_documents`：ナレッジベースのすべてのドキュメントを一覧表示
   - `pdfrag.get_system_info`：システムステータスとコンポーネントヘルスを取得
   - `pdfrag.clear_database`：ベクターデータベースをクリア（エンベディング/チャンクのみ削除）

#### MCPクエリの例

```json
{
  "question": "デバイス設定をどのようにセットアップしますか？",
  "top_k": 3
}
```

```json
{
  "pdf_path": "/path/to/technical_manual.pdf",
  "document_type": "manual"
}
```

### 出力ディレクトリを指定

```bash
python pdf_extractor.py document.pdf -o output_folder
```

### 複数ファイルを変換

```bash
python pdf_extractor.py doc1.pdf doc2.pdf doc3.pdf -o output_folder
```

### ディレクトリ全体を処理

```bash
python pdf_extractor.py /path/to/pdf/folder -o output_folder
```

### 再帰的なディレクトリ処理

```bash
python pdf_extractor.py /path/to/pdf/folder -o output_folder --recursive
```

### 詳細出力

```bash
python pdf_extractor.py document.pdf -v
```

## コマンドラインオプション

- **inputs**：変換するPDFファイルまたはディレクトリ（必須）
- **-o, --output**：出力ディレクトリ（デフォルト：現在のディレクトリの'md'）
- **-v, --verbose**：詳細ログを有効化
- **--recursive**：ディレクトリを再帰的に処理
- **--no-lint**：markdownlintの検証/修正をスキップ
- **--version**：バージョン情報を表示

## 開発

### 開発依存関係をインストール

```bash
uv pip install -e ".[dev]"
```

### テストを実行

```bash
# 基本的なPDF抽出テスト
pytest

# RAG機能テスト
python test_rag_basic.py

# 個別のRAGコンポーネントテスト
pytest tests/test_rag_engine.py
```

### コード品質

```bash
# コードをフォーマット
uv run ruff format .

# リンティングをチェック
uv run ruff check .

# 型チェック
uv run mypy pdf_extractor.py

# マークダウン出力を検証
markdownlint "**/*.md"
```

## プロジェクト構造

```text
pdf_extractor/
├── src/                  # ソースコード
│   ├── pdf_extractor/    # PDF抽出モジュール
│   │   ├── __init__.py
│   │   ├── __main__.py
│   │   ├── cli.py        # コマンドラインインターフェース
│   │   └── converter.py  # PDF変換ロジック
│   ├── rag_engine/       # RAGコンポーネント
│   │   ├── __init__.py
│   │   ├── chunking.py   # ドキュメントチャンキング戦略
│   │   ├── embeddings.py # エンベディング生成
│   │   ├── vector_store.py # ベクターデータベース操作
│   │   ├── llm_integration.py # LLM統合
│   │   └── retrieval.py  # 完全なRAGパイプライン
│   └── mcp/              # MCPサーバー実装
│       ├── __init__.py
│       ├── server.py     # フルMCPサーバー
│       └── simple_server.py # 簡易MCPサーバー
├── tests/                # テストスイート
│   ├── unit/             # ユニットテスト
│   └── integration/      # 統合テスト
├── scripts/              # ユーティリティスクリプト
├── docs/                 # ドキュメント
│   ├── setup/            # セットアップガイド
│   ├── guides/           # ユーザーガイド
│   └── technical/        # 技術ドキュメント
├── config/               # 設定ファイル
│   ├── rag_config.yaml   # RAG設定
│   ├── mcp_config.yaml   # MCPサーバー設定
│   └── logging_config.yaml # ログ設定
├── data/                 # データストレージ
│   ├── chunks/           # ドキュメントチャンク
│   ├── embeddings/       # エンベディングファイル
│   └── vector_db/        # ベクターデータベース
├── logs/                 # サーバーログ（自動作成）
├── pyproject.toml        # プロジェクト設定
├── README.md             # 英語版README
├── CLAUDE.md             # Claude固有のガイダンス
├── LICENSE               # MITライセンス
└── PRIVACY_POLICY.md     # データ使用とプライバシー
```

## エラー処理

ツールは様々なエラーシナリオを優雅に処理します：

- **ファイルが見つからない**：スキップして報告
- **無効なファイルタイプ**：PDFファイルのみを処理
- **破損したPDF**：エラーをログに記録し、他のファイルを続行
- **権限エラー**：アクセス問題を報告
- **パスワード保護されたPDF**：警告付きでスキップ

## 監視とデバッグ

### サーバーログ

MCPサーバーはデバッグと監視用のローテーティングログファイルを維持します：

- **ログの場所**：`./logs/`ディレクトリ（`MCP_LOG_DIR`で設定可能）
- **ログファイル**：
  - `mcp_server.log` - メインMCPサーバーログ
  - `simple_server.log` - 簡易MCPサーバーログ
- **ローテーションポリシー**：
  - デフォルト：ファイルあたり10MB、5つのバックアップを保持
  - 環境変数または`config/logging_config.yaml`で設定可能

### ログの表示

```bash
# 最近のログを表示
tail -f logs/mcp_server.log

# エラーを検索
grep ERROR logs/mcp_server.log

# すべてのログファイルを表示
ls -la logs/
```

### ログレベル

- **DEBUG**：デバッグ用の詳細情報
- **INFO**：一般的な情報メッセージ
- **WARNING**：潜在的な問題の警告メッセージ
- **ERROR**：失敗のエラーメッセージ
- **CRITICAL**：即座の注意が必要な重大な失敗

## 出力形式

ツールは以下を保持します：

- ドキュメント構造と見出し
- リストと箇条書き
- 適切なフォーマットのテーブル
- コードブロックと技術的なコンテンツ
- Unicodeテキスト（日本語を含む）

生成されたマークダウンファイルは、一貫したフォーマットとマークダウン標準への準拠を
確保するために、markdownlintを使用して自動的に検証および修正されます。

## 貢献

1. リポジトリをフォーク
2. 機能ブランチを作成
3. 変更を加える
4. テストと品質チェックを実行
5. プルリクエストを送信

## ライセンス

このプロジェクトはMITライセンスの下でライセンスされています - 詳細は[LICENSE](LICENSE)
ファイルを参照してください。

## サポート

問題や機能リクエストについては、
[GitHubイシュートラッカー](https://github.com/Prototype-Cafe-LLC/pdf_extractor/issues)
を使用してください。
