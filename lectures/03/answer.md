# 第3回 解答

## 演習

- 第1回（素のLLM）とエージェントの回答の違い：
- `--trace` で見えたツール呼び出し（ツール名と引数）：
- 1つの質問での LLM 呼び出し回数（`requests`）：
- 追加したツールと、docstring に書いた説明：

## 宿題

- 取り組んだレベル：実装
- やったこと：
  - `app/tools.py` に `save_learning_log(title, content)` を追加。`learning_log/` に `日時_見出し.md` として保存する（同じ名前があれば連番を付けて上書きしない。`learning_log/` は `.gitignore` 済み）
  - docstring に「保存をはっきり頼まれたときだけ使う」「ファイルを書き込むので承認が必要」と書き、`INSTRUCTIONS` にも「頼まれていないときは保存しない」を1行足した
  - `app/agent.py` で `agent.tool_plain(tools.save_learning_log, requires_approval=True)` と登録し、`output_type=[str, DeferredToolRequests]` にした
  - CLI に `run_with_approval` を追加。`result.output` が `DeferredToolRequests` の間、`approvals` の呼び出しごとにツール名と引数を表示して `[y/N]` で聞く。y なら `True`、それ以外は `ToolDenied(...)` を `DeferredToolResults` に入れ、`message_history=result.all_messages()` と一緒に `run_sync` をもう一度実行する
  - `tests/test_learning_log.py` を追加（TestModel で「承認前は書き込まれない」「y なら保存」「n なら保存されず、拒否がモデルに伝わる」を確認）。`uv run pytest -q` で 20 件すべて成功
- 結果：
  - `uv run python -m app.agent --trace "LoRAについて今日学んだことを学習ログに保存して"` の出力（実行して貼る）：

    ```text
    （ここに [approval] の表示・y/N の入力・--trace の出力を貼る）
    ```

  - y と答えた場合：`[tool return] save_learning_log -> 保存しました: learning_log/…` となり、ファイルができた。`[usage]` の `requests` は（ ）回
  - n と答えた場合：`[tool return] save_learning_log -> 利用者が実行を許可しませんでした。` がモデルに返り、ファイルはできなかった。モデルの回答は（ ）
  - 保存を頼まない質問（例：「LoRAとは？」）では save_learning_log は呼ばれなかった（実行して確認する）
- 気づき・疑問：
  - 承認待ちのとき、エージェントは例外で止まるのではなく「出力」として `DeferredToolRequests` を返す。そのため `output_type` に加える必要があり、呼び出し側（CLI）が続きを実行する責任を持つ
  - 2回目の `run_sync` には質問を渡さず、それまでの会話と承認結果だけを渡せば続きから再開できる。`usage=result.usage` を渡すと、1回目と合わせた LLM 呼び出し回数になる
  - 拒否は「何も返さない」のではなく、`ToolDenied` のメッセージがツールの結果としてモデルに届く。モデルはそれを読んで「保存しませんでした」と答えられる
  - 疑問：Web アプリや Slack のように、承認までに時間がかかる場合は、会話（`all_messages()`）をどこに保存して、どう再開するのがよいか
