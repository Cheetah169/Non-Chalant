import requests
import time
from datetime import datetime
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

TOKEN = '7040333422:AAG21UhyjwT3poez5aar9dDL_P9IELx_-z8'
URL = f'https://api.telegram.org/bot{TOKEN}/'

context_data = {}
lock = threading.Lock()

def send_message(chat_id, text):
    requests.get(URL + 'sendMessage', params={'chat_id': chat_id, 'text': text})

def send_file(chat_id, text_content, filename='results.txt'):
    bio = BytesIO()
    bio.write(text_content.encode())
    bio.seek(0)
    requests.post(
        URL + 'sendDocument',
        data={'chat_id': chat_id},
        files={'document': (filename, bio)}
    )

def get_updates(offset=None):
    params = {'timeout': 50, 'offset': offset}
    return requests.get(URL + 'getUpdates', params=params).json()

def analyze_site(url):
    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url

    result = {
        'url': url, 'payment_gateways': [], 'captcha': False,
        'cloudflare': False, 'graphql': False, 'platform': None,
        'http_status': None, 'content_type': None, 'cookies': {},
        'error': None, 'country': None
    }

    try:
        response = requests.get(url, timeout=10)
        headers = response.headers
        content_type = headers.get('Content-Type', '')
        response_text = response.text
        cookies = response.cookies.get_dict()
        country = headers.get('CF-IPCountry', 'Unknown')
        http_version = 'HTTP/1.1' if response.raw.version == 11 else 'HTTP/1.0'
        status_code = response.status_code
        reason_phrase = response.reason
        http_status = f"{http_version} {status_code} {reason_phrase}"

        result.update({
            'payment_gateways': check_for_payment_gateways(headers, response_text, cookies),
            'cloudflare': check_for_cloudflare(response_text),
            'recaptcha': check_for_captcha(response_text),
            'graphql': check_for_graphql(response_text),
            'platform': check_for_platform(response_text),
            'http_status': http_status,
            'content_type': content_type,
            'cookies': cookies,
            'country': country
        })

    except requests.Timeout:
        result['error'] = '⏰ Timeout error.'
    except Exception as e:
        result['error'] = f'❌ Error: {str(e)}'

    return result

def check_for_payment_gateways(headers, response_text, cookies):
    gateway_keywords = [
        'stripe', 'wc-braintree', 'Braintree', 'square', 'venmo', 'bitcoin', 'paypal', 'amazon-pay',
        'adyen', '2checkout', 'skrill', 'authorize.net', 'worldpay', 'payu', 'paytm',
        'afterpay', 'alipay', 'klarna', 'affirm', 'bluesnap', 'checkout.com', 'dwolla',
        'paddle', 'payoneer', 'sagepay', 'wechat pay', 'yandex.money', 'zelle',
        'shopify', 'buy now', 'add-to-cart', 'store', 'checkout', 'cart', 'shop now',
        'card', 'payment', 'gateway', 'checkout button', 'pay with'
    ]
    combined = response_text.lower() + str(headers).lower() + str(cookies).lower()
    return [kw.capitalize() for kw in gateway_keywords if kw in combined]

def check_for_cloudflare(text): return any(m in text.lower() for m in ['checking your browser', 'cf-ray', 'cloudflare'])
def check_for_captcha(text): return any(m in text.lower() for m in ['recaptcha', 'g-recaptcha'])
def check_for_graphql(text): return any(m in text.lower() for m in ['graphql', 'application/graphql'])

def check_for_platform(text):
    platforms = {
        'woocommerce': ['woocommerce', 'wc-cart', 'wc-ajax', 'wc-admin', 'wc-admin.php'],
        'magento': ['magento', 'mageplaza'],
        'shopify': ['shopify', 'myshopify'],
        'prestashop': ['prestashop', 'addons.prestashop'],
        'opencart': ['opencart', 'route=common/home'],
        'bigcommerce': ['bigcommerce', 'stencil'],
        'wordpress': ['wordpress', 'wp-content'],
        'drupal': ['drupal', 'sites/all'],
        'joomla': ['joomla', 'index.php?option=com_']
    }
    text = text.lower()
    for platform, keys in platforms.items():
        if any(k in text for k in keys):
            return platform.capitalize()
    return None

def format_analysis_results(result):
    return (
        f"🔍 𝗦𝗜𝗧𝗘 𝗔𝗡𝗔𝗟𝗬𝗦𝗜𝗦:\n"
        f"『𝗢𝗪𝗡𝗘𝗥』➜ @cheetax1\n"
        f"𝗨𝗥𝗟 ➜ {result['url']}\n"
        f"𝗣𝗔𝗬𝗠𝗘𝗡𝗧 𝗚𝗔𝗧𝗘𝗪𝗔𝗬𝗦 ➜ {', '.join(result['payment_gateways']) or 'None'}\n"
        f"𝗖𝗔𝗣𝗧𝗖𝗛𝗔 ➜ {'Yes' if result['captcha'] else 'No'}\n"
        f"𝗖𝗟𝗢𝗨𝗗𝗙𝗟𝗔𝗥𝗘 ➜ {'Yes' if result['cloudflare'] else 'No'}\n"
        f"𝗚𝗥𝗔𝗣𝗛𝗤𝗟 ➜ {'Yes' if result['graphql'] else 'No'}\n"
        f"𝗣𝗟𝗔𝗧𝗙𝗢𝗥𝗠 ➜ {result['platform'] or 'Unknown'}\n"
        f"𝗛𝗧𝗧𝗣 𝗦𝗧𝗔𝗧𝗨𝗦 ➜ {result['http_status']}\n"
        f"𝗖𝗢𝗨𝗡𝗧𝗥𝗬 ➜ {result['country']}\n"
        f"𝗘𝗥𝗥𝗢𝗥 ➜ {result['error'] or 'None'}\n"
        f"────────────────────────────\n"
    )

def handle_file(chat_id, file_content):
    for encoding in ['utf-8', 'latin-1', 'windows-1252']:
        try:
            urls = file_content.decode(encoding).splitlines()
            break
        except UnicodeDecodeError:
            continue
    else:
        send_message(chat_id, "❌ Error decoding file. Use UTF-8, Latin-1, or Windows-1252.")
        return
    context_data[chat_id] = [u.strip() for u in urls if u.strip()]
    send_message(chat_id, "✅ URLs uploaded. Use /url to start analysis.")

def handle_url_command(chat_id, text):
    if text.startswith('/url '):
        single_url = text.split(' ', 1)[1]
        result = analyze_site(single_url)
        send_message(chat_id, format_analysis_results(result))
    else:
        urls = context_data.get(chat_id)
        if not urls:
            send_message(chat_id, "❌ No URLs uploaded. Send a .txt file first.")
            return

        send_message(chat_id, f"⚡ Processing {len(urls)} URLs... Please wait.")
        start_time = datetime.now()
        results = []
        completed = 0
        total = len(urls)

        def worker(u):
            nonlocal completed
            r = analyze_site(u)
            with lock:
                completed += 1
                elapsed = datetime.now() - start_time
                est_total = (elapsed / completed) * total
                remaining = est_total - elapsed
                if completed % 50 == 0:
                    send_message(chat_id, f"⏱️ {completed}/{total} done.\nEstimated time left: {remaining.seconds}s")
            return format_analysis_results(r)

        with ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(worker, urls))

        send_file(chat_id, '\n'.join(results), 'analysis_results.txt')

def handle_start_command(chat_id):
    send_message(chat_id, "🤖 Bot Online!\nSend .txt with URLs, then /url\nSingle check: /url https://example.com")

def handle_cmds_command(chat_id):
    send_message(chat_id, "/url - Analyze uploaded URLs or single link.\n/cmds - Show commands.")

def main():
    offset = None
    while True:
        updates = get_updates(offset)
        if 'result' in updates:
            for update in updates['result']:
                offset = update['update_id'] + 1
                message = update.get('message', {})
                chat_id = message.get('chat', {}).get('id')
                text = message.get('text')
                doc = message.get('document')

                if text:
                    if text.startswith('/start'):
                        handle_start_command(chat_id)
                    elif text.startswith('/url'):
                        threading.Thread(target=handle_url_command, args=(chat_id, text)).start()
                    elif text.startswith('/cmds'):
                        handle_cmds_command(chat_id)
                elif doc:
                    file_id = doc['file_id']
                    info = requests.get(URL + 'getFile', params={'file_id': file_id}).json()
                    path = info['result']['file_path']
                    file_url = f'https://api.telegram.org/file/bot{TOKEN}/{path}'
                    file_data = requests.get(file_url).content
                    handle_file(chat_id, file_data)

if __name__ == '__main__':
    main()
