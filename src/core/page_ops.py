"""页面操作——合并、拆分、插入、删除、旋转、重排"""

import fitz
import os


class PageOps:
    """PDF页面操作"""

    @staticmethod
    def merge_pdfs(filepaths: list[str], output_path: str) -> bool:
        """合并多个PDF文件为一个"""
        try:
            merged = fitz.open()
            for fp in filepaths:
                if not os.path.exists(fp):
                    continue
                src = fitz.open(fp)
                merged.insert_pdf(src)
                src.close()
            merged.save(output_path, clean=True, garbage=4, deflate=True)
            merged.close()
            return True
        except Exception as e:
            print(f"合并失败: {e}")
            return False

    @staticmethod
    def split_pdf(doc, output_dir: str, ranges: list[tuple[int, int]]) -> list[str]:
        """拆分PDF——按页码范围提取为独立文件"""
        results = []
        try:
            for i, (start, end) in enumerate(ranges):
                out_path = os.path.join(output_dir, f"split_{i+1}.pdf")
                new_doc = fitz.open()
                for pn in range(start, min(end + 1, doc.page_count)):
                    new_doc.insert_pdf(doc, from_page=pn, to_page=pn)
                new_doc.save(out_path, clean=True, garbage=4, deflate=True)
                new_doc.close()
                results.append(out_path)
        except Exception as e:
            print(f"拆分失败: {e}")
        return results

    @staticmethod
    def insert_pdf(doc, filepath: str, after: int = -1) -> int:
        """在指定位置后插入另一个PDF的全部页面"""
        try:
            src = fitz.open(filepath)
            insert_at = after + 1 if after >= 0 else doc.page_count
            doc.insert_pdf(src, start_at=insert_at)
            src.close()
            return doc.page_count
        except Exception as e:
            print(f"插入PDF失败: {e}")
            return 0

    @staticmethod
    def insert_blank_page(doc, after: int, width: float = 595, height: float = 842) -> int:
        """在指定位置后插入空白页"""
        try:
            insert_at = after + 1 if after >= 0 else doc.page_count
            doc.new_page(insert_at, width=width, height=height)
            return doc.page_count
        except Exception as e:
            print(f"插入空白页失败: {e}")
            return 0

    @staticmethod
    def delete_pages(doc, page_nums: list[int]) -> int:
        """删除指定页面（页码排序+从后往前删除避免索引偏移）"""
        try:
            for pn in sorted(page_nums, reverse=True):
                if 0 <= pn < doc.page_count:
                    doc.delete_page(pn)
            return len(page_nums)
        except Exception as e:
            print(f"删除页面失败: {e}")
            return 0

    @staticmethod
    def rotate_pages(doc, page_nums: list[int], angle: int = 90) -> int:
        """旋转指定页面——累积旋转而非设置绝对值"""
        try:
            count = 0
            for pn in page_nums:
                if 0 <= pn < doc.page_count:
                    page = doc[pn]
                    current = page.rotation or 0
                    page.set_rotation((current + angle) % 360)
                    count += 1
            return count
        except Exception as e:
            print(f"旋转页面失败: {e}")
            return 0

    @staticmethod
    def reorder_pages(doc, new_order: list[int]) -> bool:
        """按新顺序重排页面"""
        try:
            doc.select(new_order)
            return True
        except Exception as e:
            print(f"重排页面失败: {e}")
            return False
