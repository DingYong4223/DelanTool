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


if __name__ == "__main__":
    unittest.main()
