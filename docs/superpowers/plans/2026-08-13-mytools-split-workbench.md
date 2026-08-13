# MyTools Split Workbench Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn `mytools.htm` into a responsive single/split workbench with two independent tool contexts and a compact two-row toolbar.

**Architecture:** Preserve the standalone HTML delivery model. Add a reusable workspace renderer, declarative tool registry, workspace-scoped result API, and page-level split controller inside `mytools.htm`; adapt every existing handler to receive its owning workspace instead of using global fixed IDs.

**Tech Stack:** Plain HTML/CSS/JavaScript, qrcode.js, Python 3.14 `unittest`, Playwright 1.62, installed Google Chrome.

---

## File map

- Modify: `mytools.htm` — production markup, styles, registry, workspace state, handlers, splitter, persistence, and responsive behavior.
- Create: `tests/test_mytools_split_workbench.py` — real-browser regression tests against the local HTML.
- Reference: `docs/superpowers/specs/2026-08-13-mytools-split-workbench-design.md` — approved behavior.

Keep production code in one HTML file. This repository ships the tool as a portable standalone page and does not need a build system.

### Task 1: Browser harness and semantic workbench shell

**Files:**
- Create: `tests/test_mytools_split_workbench.py`
- Modify: `mytools.htm:688-802`

- [ ] **Step 1: Write failing shell tests**

Create the test file:

```python
import pathlib
import unittest

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[1]
PAGE_URL = (ROOT / "mytools.htm").as_uri()
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

class MyToolsBrowserTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True, executable_path=CHROME)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def setUp(self):
        self.context = self.browser.new_context(viewport={"width": 1440, "height": 900})
        self.page = self.context.new_page()
        self.page.goto(PAGE_URL)

    def tearDown(self):
        self.context.close()

    def open_split(self):
        self.page.get_by_role("button", name="开启分栏").click()
        return (self.page.locator('[data-workspace-id="a"]'),
                self.page.locator('[data-workspace-id="b"]'))

    def test_starts_single_and_opens_second_workspace(self):
        self.assertEqual(self.page.locator(".tool-workspace:visible").count(), 1)
        self.page.get_by_role("button", name="开启分栏").click()
        self.assertEqual(self.page.locator(".tool-workspace:visible").count(), 2)
        self.assertEqual(self.page.get_by_role("button", name="关闭分栏").count(), 1)

    def test_compact_toolbar_has_equal_tabs_and_one_command_row(self):
        workspace = self.page.locator('[data-workspace-id="a"]')
        tabs = workspace.get_by_role("tab")
        self.assertEqual(tabs.count(), 5)
        widths = [round(tabs.nth(i).bounding_box()["width"]) for i in range(5)]
        self.assertLessEqual(max(widths) - min(widths), 1)
        self.assertEqual(workspace.locator(".tool-command-row").count(), 1)
        self.assertLessEqual(workspace.locator(".compact-toolbar").bounding_box()["height"], 70)

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests and verify the expected failure**

Run:

```bash
/Users/delanding/.local/share/mise/installs/python/3.14.3/bin/python -m unittest tests.test_mytools_split_workbench -v
```

Expected: two failures because workspaces, tabs, and split toggle do not exist.

- [ ] **Step 3: Replace legacy body markup with the shell**

Use this body structure:

```html
<body>
<main class="workbench-shell" id="WorkbenchShell">
  <header class="workbench-header">
    <div class="workbench-brand">MY TOOLS <span>/ WORKBENCH</span></div>
    <div class="workbench-header-actions">
      <span id="WorkbenchMode">单工作区 · 本地运行</span>
      <button type="button" id="SplitToggle" aria-pressed="false">开启分栏</button>
    </div>
  </header>
  <div class="workspace-stage" id="WorkspaceStage">
    <div id="WorkspaceAHost"></div>
    <div class="split-rail" id="SplitRail" role="separator"
         aria-label="调整左右工作区宽度" aria-orientation="vertical"
         aria-valuemin="30" aria-valuemax="70" aria-valuenow="50" tabindex="0">
      <span class="split-grip" aria-hidden="true">⋮</span>
    </div>
    <div id="WorkspaceBHost" hidden></div>
  </div>
</main>
</body>
```

Add `createWorkspace(id, label)`. It must create one `.tool-workspace` with `.workspace-input`, five `role="tab"` buttons, one `.tool-command-row`, `.workspace-output`, `.copy-output`, `.workspace-status`, and `.workspace-notice`. Append A and B on `DOMContentLoaded`; keep B hidden until `SplitToggle` is pressed.

- [ ] **Step 4: Add the approved compact CSS**

Use these core rules, then migrate existing syntax-color classes unchanged:

```css
:root { --deep-sea:#173247; --tool-teal:#2f7080; --rail-mint:#70d6c2; --work-white:#f7fafb; --panel-mist:#dfe8ed; --split-position:50%; --border:#c9d6dd; }
* { box-sizing:border-box; }
body { margin:0; background:var(--panel-mist); color:var(--deep-sea); font-family:"PingFang SC","Microsoft YaHei",system-ui,sans-serif; }
.workbench-header { min-height:48px; display:flex; align-items:center; justify-content:space-between; padding:0 18px; background:var(--deep-sea); color:white; }
.workspace-stage { display:grid; grid-template-columns:minmax(0,1fr); background:var(--work-white); }
.workspace-stage.split-open { grid-template-columns:minmax(0,var(--split-position)) 12px minmax(0,calc(100% - var(--split-position))); }
.tool-workspace { min-width:0; padding:16px; }
.workspace-input,.workspace-output { width:100%; border:1px solid #aabdc8; border-radius:7px; }
.workspace-output { min-height:176px; overflow:auto; background:#f0f4f6; }
.compact-toolbar { height:64px; overflow:hidden; border:1px solid var(--border); border-radius:8px; background:white; }
.tool-category-tabs { display:grid; grid-template-columns:repeat(5,minmax(0,1fr)); height:27px; }
.tool-category-tab { min-width:0; border:0; border-right:1px solid var(--border); background:#e3ebef; }
.tool-category-tab[aria-selected="true"] { background:white; color:var(--tool-teal); box-shadow:inset 0 -2px var(--tool-teal); }
.tool-command-row { display:flex; align-items:center; gap:5px; height:36px; padding:0 6px; overflow-x:auto; overflow-y:hidden; }
.tool-command { flex:0 0 auto; border:1px solid var(--border); border-radius:5px; padding:5px 8px; background:#f9fbfc; }
.tool-command[aria-pressed="true"] { border-color:var(--tool-teal); background:var(--tool-teal); color:white; }
.split-rail { display:none; align-items:center; justify-content:center; background:#d4e0e6; cursor:col-resize; touch-action:none; }
.split-open .split-rail { display:flex; }
button:focus-visible,textarea:focus-visible,[role="separator"]:focus-visible { outline:3px solid var(--rail-mint); outline-offset:2px; }
```

- [ ] **Step 5: Run tests and commit**

Expected: both tests pass.

```bash
git add mytools.htm tests/test_mytools_split_workbench.py
git commit -m "feat: add mytools workbench shell"
```

### Task 2: Declarative registry and isolated operations

**Files:**
- Modify: `mytools.htm:18-687`
- Modify: `tests/test_mytools_split_workbench.py`

- [ ] **Step 1: Add failing isolation and stable-size tests**

Add:

```python
    def test_workspaces_execute_without_cross_talk(self):
        left, right = self.open_split()
        left.locator(".workspace-input").fill('{"side":"left"}')
        right.locator(".workspace-input").fill("hello right")
        left.get_by_role("button", name="格式化", exact=True).click()
        right.get_by_role("tab", name="编解码").click()
        right.get_by_role("button", name="Base64 编码", exact=True).click()
        self.assertIn('"side"', left.locator(".workspace-output").inner_text())
        self.assertEqual(right.locator(".workspace-output").inner_text().strip(), "aGVsbG8gcmlnaHQ=")

    def test_selected_command_keeps_dimensions(self):
        workspace = self.page.locator('[data-workspace-id="a"]')
        command = workspace.get_by_role("button", name="格式化", exact=True)
        before = command.bounding_box()
        workspace.locator(".workspace-input").fill("{}")
        command.click()
        after = command.bounding_box()
        self.assertAlmostEqual(before["width"], after["width"], delta=0.5)
        self.assertAlmostEqual(before["height"], after["height"], delta=0.5)
        self.assertEqual(command.get_attribute("aria-pressed"), "true")
```

- [ ] **Step 2: Run the two tests and verify they fail**

Expected: commands or workspace-scoped handlers are absent.

- [ ] **Step 3: Register every current tool**

Add this exact registry and render only the selected category into `.tool-command-row`:

```javascript
var TOOL_REGISTRY = [
 {id:"json-format",category:"json",label:"格式化",run:Process},
 {id:"json-compress",category:"json",label:"压缩",run:JsonCompress},
 {id:"params-format",category:"json",label:"参数格式化",run:Process1},
 {id:"schema-format",category:"json",label:"Schema 格式化",run:SchemaFormat},
 {id:"base64-encode",category:"codec",label:"Base64 编码",run:Base64Encode},
 {id:"base64-decode",category:"codec",label:"Base64 解码",run:Base64Decode},
 {id:"url-encode",category:"codec",label:"URL 编码",run:UrlEncode},
 {id:"url-decode",category:"codec",label:"URL 解码",run:UrlDecode},
 {id:"html-encode",category:"codec",label:"HTML 编码",run:HtmlEncode},
 {id:"html-decode",category:"codec",label:"HTML 解码",run:HtmlDecode},
 {id:"md5-encode",category:"codec",label:"MD5 编码",run:MD5EncodeUpper},
 {id:"md5-explain",category:"codec",label:"MD5 说明",run:MD5Decode},
 {id:"timestamp-date",category:"time",label:"时间戳 → 日期",run:TimestampToDate},
 {id:"date-timestamp",category:"time",label:"日期 → 时间戳",run:DateToTimestamp},
 {id:"uppercase",category:"text",label:"转大写",run:ToUpperCase},
 {id:"lowercase",category:"text",label:"转小写",run:ToLowerCase},
 {id:"titlecase",category:"text",label:"首字母大写",run:ToTitleCase},
 {id:"char-count",category:"text",label:"字符统计",run:CharCount},
 {id:"qrcode",category:"generate",label:"生成二维码",run:GenerateQRCode}
];
```

- [ ] **Step 4: Add one workspace result API**

```javascript
function workspaceContext(root) {
  return {
    root:root,
    input:root.querySelector(".workspace-input"),
    output:root.querySelector(".workspace-output"),
    status:root.querySelector(".workspace-status"),
    notice:root.querySelector(".workspace-notice"),
    read:function(){ return this.input.value; },
    writeText:function(value){ this.output.textContent=String(value); },
    writeHtml:function(value){ this.output.innerHTML=value; },
    clear:function(){ this.output.innerHTML=""; },
    fail:function(message){ this.output.textContent=message; this.output.classList.add("output-error"); this.status.textContent="执行失败"; }
  };
}

function executeTool(root, tool) {
  var ctx=workspaceContext(root);
  ctx.output.classList.remove("output-error");
  ctx.notice.textContent="";
  try {
    tool.run(ctx);
    root.querySelectorAll(".tool-command").forEach(function(button){
      button.setAttribute("aria-pressed",button.getAttribute("data-tool-id")===tool.id?"true":"false");
    });
    ctx.status.textContent="已执行："+tool.label;
  } catch(error) { ctx.fail(tool.label+"失败："+error.message); }
}
```

- [ ] **Step 5: Convert all 19 registry handlers to accept `ctx`**

Change every registered signature to `function Name(ctx)`. Replace fixed `RawJson` reads with `ctx.read()`, fixed `Canvas` writes with `ctx.writeText`, `ctx.writeHtml`, or `ctx.clear`, and `alert` failures with `ctx.fail(...); return;`. Use `writeText` for plain results. Use this helper on every user-derived interpolation kept in formatted HTML:

```javascript
function escapeHtml(value){return String(value).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/\"/g,"&quot;").replace(/'/g,"&#39;");}
```

Replace JSON `eval` with `JSON.parse`. Preserve `ProcessObject`, syntax coloring, MD5 implementation, timestamp calculations, and Schema parsing. Ensure parameter/Schema keys and values pass through `escapeHtml`.

- [ ] **Step 6: Make QR and copy workspace-local**

Create the QR target with `document.createElement("div")`, append it under `ctx.output`, and pass the element directly to `new QRCode(target, options)`; do not assign an ID. If `QRCode` is undefined, call `ctx.fail("二维码依赖加载失败，请检查网络后重试")`.

Bind `.copy-output` to its nearest workspace. Copy only `ctx.output.innerText`, and write `复制成功`, `结果区为空`, or the failure reason into that workspace's `.workspace-notice`. Keep the hidden-textarea fallback, returning a Promise from `copyText(text)`.

- [ ] **Step 7: Run tests and commit**

Expected: all four tests pass.

```bash
git add mytools.htm tests/test_mytools_split_workbench.py
git commit -m "refactor: isolate mytools workspace operations"
```

### Task 3: Split controller, persistence, and responsive stacking

**Files:**
- Modify: `mytools.htm`
- Modify: `tests/test_mytools_split_workbench.py`

- [ ] **Step 1: Add failing interaction tests**

Add these methods:

```python
    def test_drag_clamps_and_double_click_resets(self):
        self.open_split()
        stage = self.page.locator("#WorkspaceStage")
        rail = self.page.locator("#SplitRail")
        box = stage.bounding_box()
        rail.hover()
        self.page.mouse.down()
        self.page.mouse.move(box["x"] + box["width"] * 0.9, box["y"] + 100)
        self.page.mouse.up()
        self.assertEqual(rail.get_attribute("aria-valuenow"), "70")
        rail.dblclick()
        self.assertEqual(rail.get_attribute("aria-valuenow"), "50")

    def test_keyboard_adjusts_ratio(self):
        self.open_split()
        rail = self.page.locator("#SplitRail")
        rail.focus()
        rail.press("ArrowRight")
        self.assertEqual(rail.get_attribute("aria-valuenow"), "52")
        rail.press("Home")
        self.assertEqual(rail.get_attribute("aria-valuenow"), "50")

    def test_layout_restores_without_content(self):
        left, right = self.open_split()
        right.locator(".workspace-input").fill("do not persist")
        rail = self.page.locator("#SplitRail")
        rail.focus()
        rail.press("ArrowRight")
        self.page.reload()
        self.assertEqual(self.page.locator(".tool-workspace:visible").count(), 2)
        self.assertEqual(self.page.locator("#SplitRail").get_attribute("aria-valuenow"), "52")
        self.assertEqual(self.page.locator('[data-workspace-id="b"] .workspace-input').input_value(), "")

    def test_narrow_viewport_stacks_without_overflow(self):
        self.page.set_viewport_size({"width": 720, "height": 1000})
        left, right = self.open_split()
        left_box = left.bounding_box()
        right_box = right.bounding_box()
        self.assertGreater(right_box["y"], left_box["y"] + left_box["height"] - 2)
        self.assertFalse(self.page.locator("#SplitRail").is_visible())
        self.assertEqual(self.page.evaluate("document.documentElement.scrollWidth"), 720)
```

- [ ] **Step 2: Run the interaction tests and verify failure**

Expected: ratio, persistence, and stacking assertions fail.

- [ ] **Step 3: Implement layout-only state**

```javascript
var LAYOUT_KEY="mytools.workbench.layout.v1";
var splitState={open:false,ratio:50};
function clampRatio(value){return Math.max(30,Math.min(70,Math.round(value)));}
function applySplitState(){
 var stage=document.getElementById("WorkspaceStage"), hostB=document.getElementById("WorkspaceBHost"), rail=document.getElementById("SplitRail"), toggle=document.getElementById("SplitToggle");
 splitState.ratio=clampRatio(splitState.ratio);
 stage.classList.toggle("split-open",splitState.open);
 stage.style.setProperty("--split-position",splitState.ratio+"%");
 hostB.hidden=!splitState.open;
 rail.setAttribute("aria-valuenow",String(splitState.ratio));
 toggle.setAttribute("aria-pressed",splitState.open?"true":"false");
 toggle.textContent=splitState.open?"关闭分栏":"开启分栏";
 document.getElementById("WorkbenchMode").textContent=splitState.open?"双工作区 · 本地运行":"单工作区 · 本地运行";
}
function saveSplitState(){localStorage.setItem(LAYOUT_KEY,JSON.stringify(splitState));}
function restoreSplitState(){try{var saved=JSON.parse(localStorage.getItem(LAYOUT_KEY));if(saved&&typeof saved.open==="boolean"&&typeof saved.ratio==="number"){splitState.open=saved.open;splitState.ratio=clampRatio(saved.ratio);}}catch(error){localStorage.removeItem(LAYOUT_KEY);}applySplitState();}
```

- [ ] **Step 4: Bind pointer, double-click, and keyboard controls**

On pointer down/move, compute `(event.clientX - stageRect.left) / stageRect.width * 100`, clamp, update CSS and ARIA, and save only on pointer up. Ignore pointer drag under `860px`. Double-click and `Home` reset to 50. `ArrowLeft`/`ArrowRight` adjust by 2 and save. Toggle only changes `splitState.open`; it must not recreate B or clear either workspace.

- [ ] **Step 5: Add responsive and reduced-motion CSS**

```css
@media(max-width:860px){.workbench-shell{padding:8px}.workspace-stage.split-open{grid-template-columns:minmax(0,1fr)}.split-open .split-rail{display:none}#WorkspaceBHost{border-top:1px solid #bdccd5}}
@media(prefers-reduced-motion:no-preference){.split-toggle,.tool-command{transition:background-color 140ms ease,color 140ms ease}}
```

- [ ] **Step 6: Run tests and commit**

Expected: all interaction and prior tests pass.

```bash
git add mytools.htm tests/test_mytools_split_workbench.py
git commit -m "feat: add responsive split controls"
```

### Task 4: Full registry, errors, QR, accessibility, and acceptance

**Files:**
- Modify: `mytools.htm`
- Modify: `tests/test_mytools_split_workbench.py`

- [ ] **Step 1: Add high-risk tests**

In `setUp`, initialize `self.page_errors = []` and bind `self.page.on("pageerror", lambda error: self.page_errors.append(str(error)))`. Add:

```python
    def test_invalid_json_error_is_local(self):
        left, right = self.open_split()
        left.locator(".workspace-input").fill("{")
        right.locator(".workspace-input").fill('{"ok":true}')
        left.get_by_role("button", name="格式化", exact=True).click()
        self.assertIn("JSON", left.locator(".workspace-output").inner_text())
        self.assertEqual(right.locator(".workspace-output").inner_text(), "")
        self.assertEqual(left.locator(".workspace-input").input_value(), "{")

    def test_all_tools_are_reachable_in_both_workspaces(self):
        left, right = self.open_split()
        expected = {
            "JSON": ["格式化", "压缩", "参数格式化", "Schema 格式化"],
            "编解码": ["Base64 编码", "Base64 解码", "URL 编码", "URL 解码", "HTML 编码", "HTML 解码", "MD5 编码", "MD5 说明"],
            "时间": ["时间戳 → 日期", "日期 → 时间戳"],
            "文本": ["转大写", "转小写", "首字母大写", "字符统计"],
            "生成": ["生成二维码"],
        }
        for workspace in (left, right):
            for category, commands in expected.items():
                workspace.get_by_role("tab", name=category).click()
                for command in commands:
                    self.assertEqual(workspace.get_by_role("button", name=command, exact=True).count(), 1)

    def test_qr_is_local_and_ids_are_unique(self):
        self.page.add_script_tag(content="""
          window.QRCode=function(target){
            var canvas=document.createElement('canvas');
            canvas.setAttribute('data-test-qr','true');
            target.appendChild(canvas);
          };
          window.QRCode.CorrectLevel={M:0};
        """)
        left, right = self.open_split()
        right.locator(".workspace-input").fill("right qr")
        right.get_by_role("tab", name="生成").click()
        right.get_by_role("button", name="生成二维码").click()
        self.assertEqual(right.locator('[data-test-qr="true"]').count(), 1)
        self.assertEqual(left.locator('[data-test-qr="true"]').count(), 0)
        ids = self.page.locator("[id]").evaluate_all("els => els.map(e => e.id)")
        self.assertEqual(len(ids), len(set(ids)))

    def test_core_flow_has_no_page_errors(self):
        left, right = self.open_split()
        left.locator(".workspace-input").fill("hello world")
        left.get_by_role("tab", name="编解码").click()
        left.get_by_role("button", name="URL 编码").click()
        self.page.get_by_role("button", name="关闭分栏").click()
        self.page.get_by_role("button", name="开启分栏").click()
        self.assertEqual(self.page_errors, [])

    def test_command_row_scrolls_in_narrow_pane(self):
        self.open_split()
        rail = self.page.locator("#SplitRail")
        rail.focus()
        for _ in range(10):
            rail.press("ArrowLeft")
        row = self.page.locator('[data-workspace-id="a"] .tool-command-row')
        self.page.locator('[data-workspace-id="a"]').get_by_role("tab", name="编解码").click()
        metrics = row.evaluate("el => ({client:el.clientWidth, scroll:el.scrollWidth})")
        self.assertGreater(metrics["scroll"], metrics["client"])
        row.evaluate("el => el.scrollLeft = el.scrollWidth")
        self.assertGreater(row.evaluate("el => el.scrollLeft"), 0)
```

- [ ] **Step 2: Run the new tests and verify uncovered cases fail**

Expected: at least one registry, QR, overflow, or error-state assertion fails before cleanup.

- [ ] **Step 3: Finish safe output and overflow polish**

Audit every `writeHtml` call and escape user-derived values. Give `.tool-command-row` `tabindex="0"` and an `aria-label` naming its category. After each render and resize, toggle `.has-more` using:

```javascript
function updateCommandOverflow(row){var atEnd=row.scrollLeft+row.clientWidth>=row.scrollWidth-1;row.classList.toggle("has-more",row.scrollWidth>row.clientWidth+1&&!atEnd);}
```

Keep selected/unselected borders and font weights identical so dimensions never change.

- [ ] **Step 4: Run automated verification**

```bash
/Users/delanding/.local/share/mise/installs/python/3.14.3/bin/python -m unittest tests.test_mytools_split_workbench -v
git diff --check
```

Expected: the full suite passes and `git diff --check` prints nothing.

- [ ] **Step 5: Perform real Chrome acceptance**

Serve with:

```bash
/Users/delanding/.local/share/mise/installs/python/3.14.3/bin/python -m http.server 8765
```

Open `http://localhost:8765/mytools.htm` and verify real dragging, 30/70 limits, double-click reset, 720px stacking, horizontal command scrolling, visible keyboard focus, clipboard feedback, independent A/B operations, and real qrcode.js output or its explicit CDN error. Automated tests do not replace this acceptance.

- [ ] **Step 6: Commit final polish**

```bash
git add mytools.htm tests/test_mytools_split_workbench.py
git commit -m "test: cover mytools split workbench"
```

### Task 5: Final specification review

**Files:**
- Verify: `mytools.htm`
- Verify: `tests/test_mytools_split_workbench.py`
- Verify: `docs/superpowers/specs/2026-08-13-mytools-split-workbench-design.md`

- [ ] **Step 1: Confirm scope**

Run `git status --short` and `git diff --stat HEAD~4..HEAD`. Expected production changes are limited to `mytools.htm` and the browser test; `.superpowers/` stays untracked and unstaged.

- [ ] **Step 2: Run final verification**

Run the full `unittest` command and `git diff --check HEAD~4..HEAD`. Expected: all tests pass and no whitespace errors.

- [ ] **Step 3: Check every acceptance item**

Confirm default single workspace, independent B, complete registry, no duplicate IDs, two-row toolbar, equal category widths, stable selected-command size, 30/70 drag, mouse and keyboard reset, layout-only persistence, narrow stacking, local errors/notices, QR isolation, focus visibility, and reduced motion.

- [ ] **Step 4: Report evidence boundaries**

Report automated Playwright results separately from real Chrome results. Explicitly list any dragging, scrolling, clipboard, CDN, or responsive behavior not exercised in a real browser as pending.
