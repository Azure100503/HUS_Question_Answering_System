import os
import requests
from bs4 import BeautifulSoup
import time
import urllib.parse
import argparse
from concurrent.futures import ThreadPoolExecutor
import logging
import re

# Thiết lập logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("pdf_downloader.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# def download_pdfs_from_div_pattern(url, output_folder, div_pattern="dnn_ctr\\d+_ModuleContent", delay=1):
#     """
#     Tải xuống tất cả các file PDF từ thẻ div với ID khớp với mẫu regex
#
#     Args:
#         url: URL của trang web
#         output_folder: Thư mục để lưu PDF
#         div_pattern: Mẫu regex cho ID của div chứa các link PDF
#         delay: Thời gian chờ giữa các lần tải (giây)
#
#     Returns:
#         Số lượng file PDF đã tải xuống thành công
#     """
#     # Tạo thư mục đầu ra nếu chưa tồn tại
#     if not os.path.exists(output_folder):
#         os.makedirs(output_folder)
#         logger.info(f"Đã tạo thư mục: {output_folder}")
#
#     # Thiết lập headers để tránh bị chặn
#     headers = {
#         'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
#         'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
#         'Accept-Language': 'en-US,en;q=0.5',
#         'Connection': 'keep-alive',
#         'Upgrade-Insecure-Requests': '1',
#     }
#
#     # Tải trang web
#     logger.info(f"Đang tải trang web: {url}")
#     try:
#         response = requests.get(url, headers=headers, timeout=15, verify=False)
#         response.raise_for_status()  # Kiểm tra lỗi HTTP
#     except requests.exceptions.RequestException as e:
#         logger.error(f"Lỗi khi tải trang web {url}: {e}")
#         return 0
#
#     # Parse HTML
#     soup = BeautifulSoup(response.text, 'html.parser')
#
#     # Tìm tất cả div với id khớp với mẫu (regex)
#     pattern = re.compile(div_pattern)
#     target_divs = []
#
#     # Tìm tất cả thẻ div có ID
#     for div in soup.find_all('div', id=True):
#         if pattern.match(div['id']):
#             target_divs.append(div)
#     if not target_divs:
#         logger.warning(f"Không tìm thấy div với id khớp mẫu '{div_pattern}' tại {url}")
#         return 0
#
#     logger.info(f"Tìm thấy {len(target_divs)} div khớp với mẫu tại {url}")
#
#     # Lưu trữ tất cả link PDF tìm thấy
#     all_pdf_links = []
#
#     # Tìm tất cả liên kết PDF trong các div tìm thấy
#     for div_index, target_div in enumerate(target_divs, 1):
#         pdf_links = []
#
#         # Tìm tất cả thẻ a có href chứa .pdf
#         for a_tag in target_div.find_all('a', href=True):
#             href = a_tag['href']
#             if href.lower().endswith('.pdf'):
#                 # Nếu là đường dẫn tương đối, chuyển thành tuyệt đối
#                 if not href.startswith('http'):
#                     base_url = '/'.join(url.split('/')[:3])  # Lấy domain từ URL gốc
#                     href = urllib.parse.urljoin(base_url, href)
#
#                 # Tạo tên file từ nội dung thẻ a hoặc dùng tên mặc định
#                 link_text = a_tag.get_text().strip() or f"file_{len(pdf_links) + 1}_div{div_index}"
#                 pdf_links.append((href, link_text, target_div['id']))
#
#         if pdf_links:
#             logger.info(f"Tìm thấy {len(pdf_links)} file PDF trong div '{target_div['id']}'")
#             all_pdf_links.extend(pdf_links)
#
#     if not all_pdf_links:
#         logger.warning(f"Không tìm thấy liên kết PDF nào trong bất kỳ div nào tại {url}")
#         return 0
#
#     logger.info(f"Tổng cộng: {len(all_pdf_links)} file PDF từ {len(target_divs)} div tại {url}")
#
#     # Đếm số lượng file đã tải thành công
#     success_count = 0
#
#     # Tạo thư mục con cho từng div nếu cần
#     div_folders = {}
#     create_subfolders = len(target_divs) > 1 and len(all_pdf_links) > 5
#
#     if create_subfolders:
#         for _, _, div_id in all_pdf_links:
#             if div_id not in div_folders:
#                 # Tạo tên thư mục an toàn từ div_id
#                 folder_name = div_id.replace("dnn_ctr", "module_").replace("_ModuleContent", "")
#                 div_folder = os.path.join(output_folder, folder_name)
#                 if not os.path.exists(div_folder):
#                     os.makedirs(div_folder)
#                 div_folders[div_id] = div_folder
#
#     # Tải xuống từng file PDF
#     for i, (pdf_url, pdf_name, div_id) in enumerate(all_pdf_links, 1):
#         # Tạo tên file an toàn
#         safe_name = "".join([c if c.isalnum() or c in [' ', '.', '_', '-'] else '_' for c in pdf_name])
#         safe_name = safe_name.strip()
#
#         # Nếu tên file không có đuôi .pdf, thêm vào
#         if not safe_name.lower().endswith('.pdf'):
#             safe_name += '.pdf'
#
#         # Xác định thư mục đầu ra (thư mục chính hoặc thư mục con của div)
#         target_folder = div_folders.get(div_id, output_folder) if create_subfolders else output_folder
#
#         # Đường dẫn đầy đủ để lưu file
#         output_path = os.path.join(target_folder, safe_name)
#
#         # Kiểm tra xem file đã tồn tại chưa
#         if os.path.exists(output_path):
#             logger.info(f"[{i}/{len(all_pdf_links)}] File đã tồn tại: {safe_name}")
#             success_count += 1
#             continue
#
#         # Tải file PDF
#         try:
#             logger.info(f"[{i}/{len(all_pdf_links)}] Đang tải: {pdf_url}")
#             pdf_response = requests.get(pdf_url, headers=headers, timeout=30, verify=False)
#             pdf_response.raise_for_status()
#
#             # Lưu file
#             with open(output_path, 'wb') as f:
#                 f.write(pdf_response.content)
#
#             logger.info(f"[{i}/{len(all_pdf_links)}] Đã tải xuống: {safe_name}")
#             success_count += 1
#
#             # Đợi một chút để tránh tải quá nhanh
#             time.sleep(delay)
#
#         except Exception as e:
#             logger.error(f"[{i}/{len(all_pdf_links)}] Lỗi khi tải {pdf_url}: {e}")
#
#     logger.info(f"Hoàn thành trang {url}! Đã tải {success_count}/{len(all_pdf_links)} file PDF vào {output_folder}")
#     return success_count

def download_pdfs_from_div_pattern(url, output_folder, div_pattern="dnn_ctr\\d+_ModuleContent", delay=1):
    """
    Tải xuống tất cả các file PDF từ thẻ div với ID khớp với mẫu regex

    Args:
        url: URL của trang web
        output_folder: Thư mục để lưu PDF
        div_pattern: Mẫu regex cho ID của div chứa các link PDF
        delay: Thời gian chờ giữa các lần tải (giây)

    Returns:
        Số lượng file PDF đã tải xuống thành công
    """
    # Tạo thư mục đầu ra nếu chưa tồn tại
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        logger.info(f"Đã tạo thư mục: {output_folder}")

    # Thiết lập headers để tránh bị chặn
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }

    # Tải trang web
    logger.info(f"Đang tải trang web: {url}")
    try:
        # Thêm allow_redirects=True để xử lý chuyển hướng
        response = requests.get(url, headers=headers, timeout=15, verify=False, allow_redirects=True)
        response.raise_for_status()  # Kiểm tra lỗi HTTP
    except requests.exceptions.RequestException as e:
        logger.error(f"Lỗi khi tải trang web {url}: {e}")
        return 0

    # Parse HTML
    soup = BeautifulSoup(response.text, 'html.parser')

    # Debug: Lưu HTML để kiểm tra
    with open("debug_page.html", "w", encoding="utf-8") as f:
        f.write(response.text)
    logger.info(f"Đã lưu HTML vào debug_page.html để kiểm tra")

    # Khởi tạo danh sách để lưu tất cả các liên kết PDF
    all_pdf_links = []

    # PHƯƠNG PHÁP 1: Tìm PDF trong thẻ iframe
    logger.info("Tìm kiếm PDF trong thẻ iframe...")
    iframe_tags = soup.find_all('iframe', src=True)
    for index, iframe in enumerate(iframe_tags, 1):
        src = iframe['src']
        logger.info(f"Tìm thấy iframe với src: {src}")

        # Kiểm tra xem src có phải là PDF không
        if '.pdf' in src.lower():
            # Tạo URL tuyệt đối nếu cần
            if not src.startswith('http'):
                base_url = '/'.join(url.split('/')[:3])  # Lấy domain từ URL gốc
                src = urllib.parse.urljoin(base_url, src)

            # Tìm tiêu đề nếu có
            title = None

            # Cố gắng tìm tiêu đề từ thẻ div có class="tieude" gần nhất
            parent = iframe.parent
            while parent and title is None:
                tieude_div = parent.find_previous('div', class_='tieude')
                if tieude_div:
                    a_tag = tieude_div.find('a')
                    if a_tag and a_tag.get_text().strip():
                        title = a_tag.get_text().strip()
                        break
                # Di chuyển lên một cấp
                if parent.parent:
                    parent = parent.parent
                else:
                    break

            # Nếu không tìm được tiêu đề, sử dụng tên file
            if not title:
                title = os.path.basename(src)

            logger.info(f"Tìm thấy PDF trong iframe: {title} - {src}")
            all_pdf_links.append((src, title, "iframe"))

    # PHƯƠNG PHÁP 2: Tìm theo div pattern (phương pháp gốc)
    if not all_pdf_links and div_pattern:
        logger.info(f"Tìm kiếm PDF trong div với pattern: {div_pattern}...")
        pattern = re.compile(div_pattern)
        target_divs = []

        # Tìm tất cả thẻ div có ID
        for div in soup.find_all('div', id=True):
            if pattern.search(div['id']):  # Dùng search thay vì match
                target_divs.append(div)

        if target_divs:
            logger.info(f"Tìm thấy {len(target_divs)} div khớp với mẫu tại {url}")
            # Tìm tất cả liên kết PDF trong các div tìm thấy
            for div_index, target_div in enumerate(target_divs, 1):
                # Tìm tất cả thẻ a có href chứa .pdf
                for a_tag in target_div.find_all('a', href=True):
                    href = a_tag['href']
                    if href.lower().endswith('.pdf'):
                        # Nếu là đường dẫn tương đối, chuyển thành tuyệt đối
                        if not href.startswith('http'):
                            base_url = '/'.join(url.split('/')[:3])  # Lấy domain từ URL gốc
                            href = urllib.parse.urljoin(base_url, href)

                        # Tạo tên file từ nội dung thẻ a hoặc dùng tên mặc định
                        link_text = a_tag.get_text().strip() or f"file_{len(all_pdf_links) + 1}_div{div_index}"
                        all_pdf_links.append((href, link_text, target_div['id']))
        else:
            logger.warning(f"Không tìm thấy div với id khớp mẫu '{div_pattern}' tại {url}")

    # PHƯƠNG PHÁP 3: Tìm trực tiếp tất cả liên kết PDF trong trang
    if not all_pdf_links:
        logger.info("Tìm kiếm tất cả các liên kết PDF trên trang...")
        all_links = soup.find_all('a', href=True)
        for a_tag in all_links:
            href = a_tag['href']
            if href.lower().endswith('.pdf'):
                # Nếu là đường dẫn tương đối, chuyển thành tuyệt đối
                if not href.startswith('http'):
                    base_url = '/'.join(url.split('/')[:3])  # Lấy domain từ URL gốc
                    href = urllib.parse.urljoin(base_url, href)

                link_text = a_tag.get_text().strip() or f"file_{len(all_pdf_links) + 1}"
                # Dùng "general" làm ID div vì không có div cụ thể
                all_pdf_links.append((href, link_text, "general"))

    if not all_pdf_links:
        logger.warning(f"Không tìm thấy liên kết PDF nào trong trang web: {url}")
        return 0

    logger.info(f"Tổng cộng: {len(all_pdf_links)} file PDF tìm thấy tại {url}")

    # Tạo thư mục con cho từng div nếu cần
    div_folders = {}
    create_subfolders = len(set([div_id for _, _, div_id in all_pdf_links])) > 1 and len(all_pdf_links) > 5

    if create_subfolders:
        for _, _, div_id in all_pdf_links:
            if div_id not in div_folders:
                # Tạo tên thư mục an toàn từ div_id
                folder_name = re.sub(r'[^\w\-_]', '_', div_id)
                div_folder = os.path.join(output_folder, folder_name)
                if not os.path.exists(div_folder):
                    os.makedirs(div_folder)
                div_folders[div_id] = div_folder

    # Đếm số lượng file đã tải thành công
    success_count = 0

    # Tải xuống từng file PDF
    for i, (pdf_url, pdf_name, div_id) in enumerate(all_pdf_links, 1):
        # Tạo tên file an toàn
        safe_name = "".join([c if c.isalnum() or c in [' ', '.', '_', '-'] else '_' for c in pdf_name])
        safe_name = safe_name.strip()

        # Nếu tên file không có đuôi .pdf, thêm vào
        if not safe_name.lower().endswith('.pdf'):
            safe_name += '.pdf'

        # Xác định thư mục đầu ra (thư mục chính hoặc thư mục con của div)
        target_folder = div_folders.get(div_id, output_folder) if create_subfolders else output_folder

        # Đường dẫn đầy đủ để lưu file
        output_path = os.path.join(target_folder, safe_name)

        # Kiểm tra xem file đã tồn tại chưa
        if os.path.exists(output_path):
            logger.info(f"[{i}/{len(all_pdf_links)}] File đã tồn tại: {safe_name}")
            success_count += 1
            continue

        # Tải file PDF
        try:
            logger.info(f"[{i}/{len(all_pdf_links)}] Đang tải: {pdf_url}")
            pdf_response = requests.get(pdf_url, headers=headers, timeout=30, verify=False, allow_redirects=True)

            # Kiểm tra Content-Type
            content_type = pdf_response.headers.get('Content-Type', '').lower()

            # Kiểm tra nếu là PDF hoặc application/octet-stream hoặc URL có đuôi .pdf
            if 'application/pdf' in content_type or 'application/octet-stream' in content_type or pdf_url.lower().endswith(
                    '.pdf'):
                # Lưu file
                with open(output_path, 'wb') as f:
                    f.write(pdf_response.content)

                logger.info(f"[{i}/{len(all_pdf_links)}] Đã tải xuống: {safe_name}")
                success_count += 1
            else:
                logger.warning(f"[{i}/{len(all_pdf_links)}] Không phải PDF: {pdf_url} (Content-Type: {content_type})")

                # Lưu nội dung để kiểm tra
                debug_file = os.path.join(target_folder, f"debug_{i}_{safe_name}.txt")
                with open(debug_file, 'wb') as f:
                    f.write(pdf_response.content[:1000])  # Lưu phần đầu để kiểm tra
                logger.info(f"Đã lưu phần đầu của phản hồi vào {debug_file}")

            # Đợi một chút để tránh tải quá nhanh
            time.sleep(delay)

        except Exception as e:
            logger.error(f"[{i}/{len(all_pdf_links)}] Lỗi khi tải {pdf_url}: {e}")

    logger.info(f"Hoàn thành trang {url}! Đã tải {success_count}/{len(all_pdf_links)} file PDF vào {output_folder}")
    return success_count


def process_url_list(urls, output_folder, div_pattern="dnn_ctr\\d+_ModuleContent", max_workers=3, delay=1):
    """
    Xử lý một danh sách URL để tải xuống các file PDF

    Args:
        urls: Danh sách các URL cần xử lý
        output_folder: Thư mục để lưu PDF
        div_pattern: Mẫu regex cho ID của div chứa các link PDF
        max_workers: Số luồng đồng thời tối đa
        delay: Thời gian chờ giữa các lần tải (giây)
    """
    total_pdfs = 0

    # Sử dụng ThreadPoolExecutor để xử lý nhiều URL cùng lúc
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Tạo các futures cho mỗi URL
        futures = {executor.submit(download_pdfs_from_div_pattern, url, output_folder, div_pattern, delay): url for url
                   in urls}

        # Xử lý kết quả khi hoàn thành
        for future in futures:
            url = futures[future]
            try:
                pdfs_count = future.result()
                total_pdfs += pdfs_count
            except Exception as e:
                logger.error(f"Lỗi không xác định khi xử lý {url}: {e}")

    logger.info(f"Tổng cộng đã tải xuống {total_pdfs} file PDF từ {len(urls)} trang web")


def read_urls_from_file(file_path):
    """
    Đọc danh sách URL từ file

    Args:
        file_path: Đường dẫn đến file chứa URL (mỗi URL một dòng)

    Returns:
        Danh sách các URL
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
        logger.info(f"Đã đọc {len(urls)} URL từ file {file_path}")
        return urls
    except Exception as e:
        logger.error(f"Lỗi khi đọc file URL {file_path}: {e}")
        return []


def main():
    parser = argparse.ArgumentParser(description='Tải xuống các file PDF từ nhiều trang web.')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-u', '--url', help='URL của trang web cần tải PDF')
    group.add_argument('-f', '--file', help='File chứa danh sách URL (mỗi URL một dòng)')
    group.add_argument('-l', '--urls', nargs='+', help='Danh sách các URL cách nhau bởi khoảng trắng')

    parser.add_argument('-o', '--output', default='downloaded_pdfs', help='Thư mục đầu ra (mặc định: downloaded_pdfs)')
    parser.add_argument('-d', '--div-pattern', default='dnn_ctr\\d+_ModuleContent',
                        help='Mẫu regex cho ID của div (mặc định: dnn_ctr\\d+_ModuleContent)')
    parser.add_argument('-w', '--workers', type=int, default=3, help='Số luồng đồng thời tối đa (mặc định: 3)')
    parser.add_argument('-t', '--delay', type=float, default=1.0,
                        help='Thời gian chờ giữa các lần tải (giây, mặc định: 1.0)')

    args = parser.parse_args()

    # Xác định danh sách URL cần xử lý
    urls = []
    if args.url:
        urls = [args.url]
    elif args.file:
        urls = read_urls_from_file(args.file)
    elif args.urls:
        urls = args.urls

    if not urls:
        logger.error("Không có URL nào để xử lý.")
        return

    # Xử lý các URL
    process_url_list(urls, args.output, args.div_pattern, args.workers, args.delay)


if __name__ == "__main__":
    # Tắt cảnh báo liên quan đến việc bỏ qua xác thực SSL
    import warnings
    import urllib3

    warnings.filterwarnings('ignore', category=urllib3.exceptions.InsecureRequestWarning)

    main()