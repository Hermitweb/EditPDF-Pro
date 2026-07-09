"""页面操作——合并、拆分、插入、删除、旋转"""

import fitz
import os
import tempfile


class PageOps:
    """PDF页面管理操作"""

    @staticmethod
    def merge_pdfs(filepaths: list[str], output_path: str) -> int:
        """合并多个PDF，返回总页数"""
        result = fitz.open()
        try:
            total_pages = 0
            for fp in filepaths:
                if not os.path.exists(fp):
                    continue
                src = fitz.open(fp)
                result.insert_pdf(src)
                total_pages += src.page_count
                src.close()

            result.save(output_path, clean=True, garbage=4)
            return total_pages
        finally:
            result.close()

    @staticmethod
    def split_pdf(doc, output_dir: str,
                  ranges: list[tuple[int, int]]) -> list[str]:
        """按页面范围拆分PDF，返回输出文件路径列表"""
        output_files = []
        try:
            for i, (start, end) in enumerate(ranges):
                new_doc = fitz.open()
                new_doc.insert_pdf(doc, from_page=start, to_page=end)
                out_path = os.path.join(
                    output_dir, f"拆分_{i + 1}_第{start + 1}-{end + 1}页.pdf"
                )
                new_doc.save(out_path, clean=True, garbage=4)
                new_doc.close()
                output_files.append(out_path)
            return output_files
        except Exception as e:
            # 清理已创建的文件
            for f in output_files:
                try:
                    os.remove(f)
                except OSError:
                    pass
            raise e

    @staticmethod
    def extract_pages(doc, page_nums: list[int],
                      output_path: str) -> int:
        """提取指定页面为新PDF，返回页数"""
        new_doc = fitz.open()
        try:
            for p in page_nums:
                if 0 <= p < doc.page_count:
                    new_doc.insert_pdf(doc, from_page=p, to_page=p)
            new_doc.save(output_path, clean=True, garbage=4)
            return new_doc.page_count
        finally:
            new_doc.close()

    @staticmethod
    def insert_pdf(doc, insert_path: str, after_page: int) -> int:
        """在指定页后插入另一个PDF，返回插入的页数"""
        src = fitz.open(insert_path)
        pages = src.page_count
        # 在 after_page 后插入
        doc.insert_pdf(src, start_at=after_page + 1)
        src.close()
        return pages

    @staticmethod
    def insert_blank_page(doc, after_page: int,
                          width: float = 595, height: float = 842) -> int:
        """插入空白页（默认A4: 595x842点），返回新页索引"""
        new_page = doc.new_page(
            width=width, height=height
        )
        # 移动到最后插入的位置
        last_idx = doc.page_count - 1
        if after_page + 1 < last_idx:
            doc.move_page(last_idx, after_page + 1)
        return after_page + 1

    @staticmethod
    def delete_pages(doc, page_nums: list[int]) -> int:
        """删除指定页面，返回删除数量"""
        # 从大到小排序，避免索引偏移
        sorted_nums = sorted(set(page_nums), reverse=True)
        count = 0
        for p in sorted_nums:
            if 0 <= p < doc.page_count:
                doc.delete_page(p)
                count += 1
        return count

    @staticmethod
    def rotate_pages(doc, page_nums: list[int],
                     angle: int = 90) -> int:
        """旋转指定页面，返回旋转数量"""
        count = 0
        for p in page_nums:
            if 0 <= p < doc.page_count:
                doc[p].set_rotation(angle)
                count += 1
        return count

    @staticmethod
    def reorder_pages(doc, new_order: list[int]) -> bool:
        """重排页面顺序（拖拽排序后调用）"""
        if len(new_order) != doc.page_count:
            return False
        if sorted(new_order) != list(range(doc.page_count)):
            return False
        # 通过逐页移动实现
        current_page = 0
        for target_pos in new_order:
            if target_pos != current_page:
                doc.move_page(target_pos, current_page)
            current_page += 1
        return True
