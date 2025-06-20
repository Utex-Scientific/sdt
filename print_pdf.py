from playwright.sync_api import sync_playwright

HEADER_HTML = """
<div style="font-size: 10px; padding-right: 1em; text-align: right; width: 100%;">
</div>
"""

FOOTER_HTML = """
<div style="font-size: 10px; margin-left: 4em; margin-right: 4em; width: 100%;">
    <p style="float:left">Copyright &copy; 2025 UTEX Scientific Instruments Inc</p>
    <p style="float:right"><span class="pageNumber"></span>/<span class="totalPages"></span></p>
</div>
"""


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--disable-gpu", "--disable-dev-shm-usage"])
        page = browser.new_page()
        page.goto("http://localhost:8000/iwh5/print_page")
        # Mathjax render works on second load in local browsers for some reason
        page.reload()
        page.pdf(
            path="public/IWH5-UserManual.pdf",
            display_header_footer=True,
            header_template=HEADER_HTML,
            footer_template=FOOTER_HTML,
            print_background=True,
            format="Letter",
            scale=1,
            margin={
                "top": "80",
                "bottom": "80",           
                "left": "40",
                "right": "40"
            }
        )
        browser.close()


if __name__ == "__main__":
    main()
