from bs4 import BeautifulSoup
import requests
import time
import os
import random
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def setup_session():
    # Tạo session với cấu hình retry
    session = requests.Session()

    # Cấu hình retry với backoff để thử lại khi bị lỗi
    retry_strategy = Retry(
        total=3,  # Số lần thử lại tối đa
        status_forcelist=[429, 500, 502, 503, 504],  # Mã lỗi cần thử lại
        backoff_factor=1,  # Hệ số trì hoãn (1s, 2s, 4s, ...)
        respect_retry_after_header=True  # Tôn trọng header Retry-After
    )

    # Áp dụng chiến lược retry cho tất cả các request HTTP/HTTPS
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    # Thêm User-Agent để trang web không nghi ngờ là bot
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',
        'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    })

    return session


def get_links(url, output_file, session):
    try:
        # Trì hoãn ngẫu nhiên từ 2-5 giây trước mỗi request
        delay = random.uniform(2, 5)
        print(f"Đợi {delay:.2f} giây trước khi truy cập {url}...")
        time.sleep(delay)

        print(f"Đang truy cập {url}...")
        response = session.get(url, verify=False, timeout=10)

        # Kiểm tra trạng thái response
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Tìm thẻ <div> có id là "jquery-accordion-menu-header"
        menu_div = soup.find("div", {"id": "jquery-accordion-menu-header"})

        # Nếu không tìm thấy, thử tìm các container menu khác
        if not menu_div:
            menu_div = soup.find("div", {"id": "jquery-accordion-menu"})

        # Lấy tất cả các link trong thẻ <div> này
        links = [a['href'] for a in menu_div.find_all('a', href=True)] if menu_div else []

        # Tạo thư mục đầu ra nếu chưa tồn tại
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            # In danh sách các link
            if not links:
                print(f"Không tìm thấy liên kết nào trong {url}")
                f.write(f"# Không tìm thấy liên kết nào trong {url}\n")
            else:
                count = 0
                for link in links:
                    if link.startswith('https') or link.startswith('http'):
                        f.write(link + '\n')
                        count += 1
                    elif link.startswith('/'):
                        # Xử lý đường dẫn tương đối
                        base_url = '/'.join(url.split('/')[:3])  # Lấy phần domain
                        full_link = base_url + link
                        f.write(full_link + '\n')
                        count += 1
                print(f"Đã lưu {count} liên kết từ {url}")

        return True

    except requests.exceptions.RequestException as e:
        print(f"Lỗi khi truy cập {url}: {e}")
        with open("error_log.txt", "a", encoding='utf-8') as error_file:
            error_file.write(f"{url}: {str(e)}\n")
        return False

def get_news_links(url, output_file, session):
    try:
        # Trì hoãn ngẫu nhiên từ 2-5 giây trước mỗi request
        delay = random.uniform(2, 5)
        print(f"Đợi {delay:.2f} giây trước khi truy cập {url}...")
        time.sleep(delay)

        print(f"Đang truy cập {url}...")
        response = session.get(url, verify=False, timeout=10)

        # Kiểm tra trạng thái response
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Tìm thẻ <div> có id là "jquery-accordion-menu-header"
        menu_div = soup.find("div", {"id": "dnn_ctr10921_ModuleContent"})

        # Nếu không tìm thấy, thử tìm các container menu khác
        # if not menu_div:
        #     menu_div = soup.find("div", {"id": "jquery-accordion-menu"})


        # Lấy tất cả các link trong thẻ <div> này
        links = [a['href'] for div in menu_div.find_all("div", class_="item-image") for a in
                 div.find_all('a', href=True)] if menu_div else []

        # Tạo thư mục đầu ra nếu chưa tồn tại
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        with open(output_file, 'a', encoding='utf-8') as f:
            # In danh sách các link
            if not links:
                print(f"Không tìm thấy liên kết nào trong {url}")
                f.write(f"# Không tìm thấy liên kết nào trong {url}\n")
            else:
                count = 0
                for link in links:
                    if link.startswith('https') or link.startswith('http'):
                        f.write(link + '\n')
                        count += 1
                    elif link.startswith('/'):
                        # Xử lý đường dẫn tương đối
                        base_url = '/'.join(url.split('/')[:3])  # Lấy phần domain
                        full_link = base_url + link
                        f.write(full_link + '\n')
                        count += 1
                print(f"Đã lưu {count} liên kết từ {url}")

        return True

    except requests.exceptions.RequestException as e:
        print(f"Lỗi khi truy cập {url}: {e}")
        with open("error_log.txt", "a", encoding='utf-8') as error_file:
            error_file.write(f"{url}: {str(e)}\n")
        return False


def main():
    # Danh sách các URL cần truy cập
    urls_and_outputs = [
        # ("https://hus.vnu.edu.vn/gioi-thieu.html", "data/hus_page_urls/gioi_thieu.txt"),
        # ("https://hus.vnu.edu.vn/khoa-hoc-cong-nghe.html", "data/hus_page_urls/khcn.txt"),
        # ("https://hus.vnu.edu.vn/hop-tac-va-phat-trien.html", "data/hus_page_urls/hop_tac_phat_trien.txt"),
        # ("https://hus.vnu.edu.vn/hoc-sinh-sinh-vien.html", "data/hus_page_urls/hssv.txt"),
        # ("https://hus.vnu.edu.vn/tai-lieu-bieu-mau.html", "data/hus_page_urls/tai_lieu_bieu_mau.txt")
        ("https://hus.vnu.edu.vn/dao-tao.html", "data/hus_page_urls/dao_tao.txt")
    ]
    urls = ["https://hus.vnu.edu.vn/tin-tuc-su-kien/tin-moi-nhat.html"]
    news_output = "links/tin_tuc_su_kien.txt"




    # Khởi tạo session một lần và tái sử dụng
    session = setup_session()
    # Crawl phần tin tức sự kiên
    # for url in urls:
    #     success = get_news_links(url, news_output, session)
    #     if not success:
    #         print(f"Đang tạm dừng 30 giây sau khi gặp lỗi...")
    #         time.sleep(30)  # Tạm dừng lâu hơn nếu gặp lỗi
    #

    # Xử lý từng URL
    for url, output_file in urls_and_outputs:
        success = get_links(url, output_file, session)
        if not success:
            print(f"Đang tạm dừng 30 giây sau khi gặp lỗi...")
            time.sleep(30)  # Tạm dừng lâu hơn nếu gặp lỗi


if __name__ == "__main__":
    main()