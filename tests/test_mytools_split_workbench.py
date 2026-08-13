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
        cls.browser = cls.playwright.chromium.launch(
            headless=True,
            executable_path=CHROME,
        )

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def setUp(self):
        self.context = self.browser.new_context(
            viewport={"width": 1440, "height": 900}
        )
        self.page = self.context.new_page()
        self.page.set_default_timeout(3000)
        self.page.goto(PAGE_URL)

    def tearDown(self):
        self.context.close()

    def open_split(self):
        self.page.get_by_role("button", name="开启分栏").click()
        return (
            self.page.locator('[data-workspace-id="a"]'),
            self.page.locator('[data-workspace-id="b"]'),
        )

    def test_starts_single_and_opens_second_workspace(self):
        self.assertEqual(self.page.locator(".tool-workspace:visible").count(), 1)
        self.page.get_by_role("button", name="开启分栏").click()
        self.assertEqual(self.page.locator(".tool-workspace:visible").count(), 2)
        self.assertEqual(
            self.page.get_by_role("button", name="关闭分栏").count(), 1
        )

    def test_compact_toolbar_has_equal_tabs_and_one_command_row(self):
        workspace = self.page.locator('[data-workspace-id="a"]')
        tabs = workspace.get_by_role("tab")
        self.assertEqual(tabs.count(), 5)
        widths = [round(tabs.nth(i).bounding_box()["width"]) for i in range(5)]
        self.assertLessEqual(max(widths) - min(widths), 1)
        self.assertEqual(workspace.locator(".tool-command-row").count(), 1)
        self.assertLessEqual(
            workspace.locator(".compact-toolbar").bounding_box()["height"], 70
        )

    def test_workspaces_execute_without_cross_talk(self):
        left, right = self.open_split()
        left.locator(".workspace-input").fill('{"side":"left"}')
        right.locator(".workspace-input").fill("hello right")
        left.get_by_role("button", name="格式化", exact=True).click()
        right.get_by_role("tab", name="编解码").click()
        right.get_by_role("button", name="Base64 编码", exact=True).click()
        self.assertIn('"side"', left.locator(".workspace-output").inner_text())
        self.assertEqual(
            right.locator(".workspace-output").inner_text().strip(),
            "aGVsbG8gcmlnaHQ=",
        )

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

    def test_copy_button_targets_only_its_workspace(self):
        self.context.grant_permissions(["clipboard-read", "clipboard-write"])
        left, right = self.open_split()
        left.locator(".workspace-input").fill("left")
        right.locator(".workspace-input").fill("right")
        left.get_by_role("tab", name="文本").click()
        right.get_by_role("tab", name="文本").click()
        left.get_by_role("button", name="转大写").click()
        right.get_by_role("button", name="转大写").click()
        right.get_by_role("button", name="复制结果").click()
        self.assertEqual(self.page.evaluate("navigator.clipboard.readText()"), "RIGHT")
        self.assertIn("复制成功", right.locator(".workspace-notice").inner_text())
        self.assertEqual(left.locator(".workspace-notice").inner_text(), "")

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
        self.assertEqual(
            self.page.locator("#SplitRail").get_attribute("aria-valuenow"), "52"
        )
        self.assertEqual(
            self.page.locator('[data-workspace-id="b"] .workspace-input').input_value(),
            "",
        )

    def test_narrow_viewport_stacks_without_overflow(self):
        self.page.set_viewport_size({"width": 720, "height": 1000})
        left, right = self.open_split()
        left_box = left.bounding_box()
        right_box = right.bounding_box()
        self.assertGreater(
            right_box["y"], left_box["y"] + left_box["height"] - 2
        )
        self.assertFalse(self.page.locator("#SplitRail").is_visible())
        self.assertEqual(self.page.evaluate("document.documentElement.scrollWidth"), 720)


if __name__ == "__main__":
    unittest.main()
