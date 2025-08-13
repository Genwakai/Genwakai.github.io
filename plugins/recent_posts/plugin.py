import re
from collections.abc import Callable
import mkdocs
from mkdocs.config.config_options import Type
from mkdocs.structure.files import File, Files
from mkdocs.structure.pages import Page

class RecentPostsConfig(mkdocs.config.base.Config):
    enabled = Type(bool, default = True)
    blogs = Type(list, default = [])

class RecentPostsPlugin(mkdocs.plugins.BasePlugin[RecentPostsConfig]):
    surpports_multiple_instances = True

    # Initialize plugin
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Initialize incremental builds
        self.is_serve = False
        self.is_dirty = False

    def on_page_markdown(self, markdown:str, page:Page, config, files:Files):
        if not page.url in [""]+[blog+"/" for blog in self.config.blogs]:
            return
        for blog in self.config.blogs:
            # print(blog)
            posts = []
            for file in files:
                uri:str = file.src_uri
                if not (uri.startswith(blog) and uri.endswith(".md") and uri.count("/") > 1):
                    continue
                frontmatter = file.content_string.split("---")[1]
                m = re.search(r"date:\s*(\d{4}-\d{2}-\d{2})", frontmatter)
                if m.groups().__len__() != 1:
                    raise RuntimeError(uri+"の date フロントマターのフォーマットが不適切です。\n`date: 2025-04-01` の形で記入してください。")
                datestr:str = m.groups()[0]
                dateint = int(datestr.replace("-",""))
                posts.append({"dateint":dateint, "file":file})
            posts.sort(key = lambda post: post["dateint"], reverse=True)
            m = re.search(r"RECENT_POSTS\(\s*"+blog+r"(\s*,\s*(\d+))?\s*\)", markdown)
            # print(r"RECENT_POSTS\(\s*" + blog + r"(\s*,\s*(\d+))?\s*\)")
            if not m:
                return
            if (posts_num := m.groups()[1]) != None:
                # posts_num = int(m.groups()[1])
                recent_posts = posts[:int(posts_num)]
            else:
                recent_posts = posts
            # print(m.group())
            mdlist = ""
            for post in recent_posts:
                mdlist += self._md_list_item(post["file"], page.url)+"\n"
            mdcontent = '<div class="grid cards recent_posts" markdown>\n'+mdlist+'</div>'
            markdown = markdown.replace(m.group(), mdcontent)
        return markdown

    def _md_list_item(self, file:File, url:str):
        frontmatter = file.content_string.split("---")[1]
        m = re.search(r"date:\s*(\d{4})-(\d{2})-(\d{2})", frontmatter)
        datestr = f"{int(m.groups()[0])}年{int(m.groups()[1])}月{int(m.groups()[2])}日"
        m = re.search(r"#\s+(.+)\n", file.content_string)
        if not m or m.groups().__len__() != 1:
            raise RuntimeError("ポストのタイトルが不適切です。\n`# タイトル`の形で記入してください。")
        title = m.groups()[0]
        link = "./"+file.src_uri.replace(url,"")
        # print(link)
        return f'-   <span class="recent_posts_date">{datestr}</span>  \n    [{title}]({link})'
