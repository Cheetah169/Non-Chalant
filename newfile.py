import requests
import time
from datetime import datetime
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor
import threading
import sys
import traceback

TOKEN = "7040333422:AAHUF7yNM5gClaKEo7uLG4UCblfnKtYuIUA"
URL = f'https://api.telegram.org/bot{TOKEN}/'

context_data = {}
lock = threading.Lock()

def send_message(chat_id, text):
    try:
        response = requests.get(URL + 'sendMessage', params={'chat_id': chat_id, 'text': text})
        return response.json().get('result', {}).get('message_id')
    except Exception as e:
        print(f"Error sending message: {e}")
        return None

def edit_message(chat_id, message_id, text):
    try:
        requests.get(URL + 'editMessageText', params={
            'chat_id': chat_id, 
            'message_id': message_id, 
            'text': text
        })
    except Exception as e:
        print(f"Error editing message: {e}")

def send_file(chat_id, text_content, filename='results.txt'):
    try:
        bio = BytesIO()
        bio.write(text_content.encode())
        bio.seek(0)
        requests.post(
            URL + 'sendDocument',
            data={'chat_id': chat_id},
            files={'document': (filename, bio)}
        )
    except Exception as e:
        print(f"Error sending file: {e}")

def get_updates(offset=None):
    params = {'timeout': 50, 'offset': offset}
    try:
        return requests.get(URL + 'getUpdates', params=params).json()
    except Exception as e:
        print(f"Error getting updates: {e}")
        return {}

def analyze_site(url):
    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url

    result = {
        'url': url, 'payment_gateways': [], 'protection': 'Maybe clean',
        'platform': 'Unknown', 'time_taken': 0, 'error': None
    }

    start_time = time.time()
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9',
            'Accept-Language': 'en-US,en;q=0.5',
        }
        response = requests.get(url, headers=headers, timeout=10)
        response_headers = response.headers
        response_text = response.text
        cookies = response.cookies.get_dict()
        
        end_time = time.time()
        result['time_taken'] = round(end_time - start_time, 2)

        result.update({
            'payment_gateways': check_for_payment_gateways(response_headers, response_text, cookies),
            'protection': check_for_protection(response_text, response_headers),
            'platform': check_for_platform(response_text)
        })

    except requests.Timeout:
        result['error'] = 'Timeout'
        result['time_taken'] = round(time.time() - start_time, 2)
    except Exception as e:
        result['error'] = str(e)
        result['time_taken'] = round(time.time() - start_time, 2)

    return result

def check_for_payment_gateways(headers, response_text, cookies):
    gateway_signatures = {
        'PayPal': ['paypal', 'paypal.com', 'paypal-checkout', 'wc-paypal', 'paypal_standard'],
    'Stripe': ['stripe', 'stripe.com', 'stripe.js', 'sk_live_', 'pk_live_', 'checkout.stripe.com', 'wc-stripe'],
    'Braintree': ['braintree', 'braintreepayments', 'braintree-api', 'braintree-web', 'wc-braintree'],
    'Square': ['squareup.com', 'square-checkout', 'checkout.squareup.com', 'api.squareup.com', 'square-gateway', 'square-payment', 'square_app_id', 'squareLocationId', 'square-form'], 
    'Authorize.net': ['authorize.net', 'authorizenet', 'api.authorize.net', 'accept.authorize.net', 'wc-authorize-net'],
    'Adyen': ['adyen', 'adyen.com', 'checkoutshopper-live.adyen.com', 'wc-adyen'],
    'Worldpay': ['worldpay', 'worldpay.com', 'secure.worldpay.com', 'wc-worldpay'],
    'Shopify Payments': ['shopify', 'shopify-payments', 'shopify-checkout'],
    'Razorpay': ['razorpay', 'razorpay.com', 'api.razorpay.com', 'wc-razorpay'],
    'NMI': ['nmi', 'nmi.com', 'secure.nmi.com', 'merchantequip.com', 'wc-nmi'],
    'PayU': ['payu', 'payu.com', 'secure.payu.com', 'payulatam', 'wc-payu'],
    'Payzeey': ['payzeey', 'payzeey.com'],
    'Payflow': ['payflow', 'payflowpro', 'payflowlink', 'paypal payflow', 'wc-payflow'],
    'Kashier': ['kashier', 'kashier.io', 'api.kashier.io'],
    '2Checkout': ['2checkout', '2co.com', '2checkout.com', 'wc-2checkout'],
    'BlueSnap': ['bluesnap', 'bluesnap.com', 'ws.bluesnap.com', 'wc-bluesnap'],
    'Paysafe': ['paysafe', 'paysafe.com', 'paysafecard', 'netbanx'],
    'Skrill': ['skrill', 'skrill.com', 'pay.skrill.com', 'wc-skrill'],
    'Neteller': ['neteller', 'neteller.com'],
    'Payoneer': ['payoneer', 'payoneer.com'],
    'Instamojo': ['instamojo', 'instamojo.com', 'api.instamojo.com', 'wc-instamojo'],
    'Flutterwave': ['flutterwave', 'flutterwave.com', 'checkout.flutterwave.com', 'wc-flutterwave'],
    'Paystack': ['paystack', 'paystack.com', 'api.paystack.co', 'wc-paystack'],
    'CoinPayments': ['coinpayments', 'coinpayments.net', 'api.coinpayments.net', 'wc-coinpayments'],
    'Dwolla': ['dwolla', 'dwolla.com', 'api.dwolla.com'],
    'Splitit': ['splitit', 'splitit.com'],
    'GoCardless': ['gocardless', 'gocardless.com', 'wc-gocardless'],
    'Payline': ['payline', 'payline.com', 'api.payline.com'],
    'ProPay': ['propay', 'propay.com', 'api.propay.com'],
    'eWay': ['eway', 'eway.com.au', 'api.ewaypayments.com', 'wc-eway'],
    'CyberSource': ['cybersource', 'cybersource.com', 'secureacceptance', 'api.cybersource.com', 'wc-cybersource'],
    'Recurly': ['recurly', 'recurly.com', 'api.recurly.com'],
    'Moneris': ['moneris', 'moneris.com', 'esqa.moneris.com', 'checkout.moneris.com', 'wc-moneris'],
    'Zuora': ['zuora', 'zuora.com', 'rest.apis.zuora.com'],
    'Converge': ['converge', 'convergepay', 'convergepay.com', 'api.convergepay.com', 'wc-converge'],
    'Payeezy': ['payeezy', 'payeezy.com', 'api.payeezy.com', 'firstdata', 'wc-payeezy'],    
    'eXact Payments': ['exact', 'exact.com', 'hostedpage.exactpay.com', 'api.exactpay.com'],
    'Chase Paymentech': ['chase paymentech', 'chase.com', 'secure.paymentech.com', 'wc-chase']
    }

    combined = response_text.lower() + str(headers).lower() + str(cookies).lower()
    found_gateways = []
    
    for gateway_name, signatures in gateway_signatures.items():
        if any(sig in combined for sig in signatures):
            found_gateways.append(gateway_name)
    
    # Check for generic payment indicators if no specific gateways found
    payment_indicators = ['buy now', 'add-to-cart', 'checkout', 'cart', 'shop now', 'payment']
    if any(indicator in combined for indicator in payment_indicators) and not found_gateways:
        found_gateways.append('Generic Payment')
    
    return found_gateways

def check_for_protection(text, headers):
    text_lower = text.lower()
    headers_str = str(headers).lower()
    
    protections = []
    
    # Check for Cloudflare
    cloudflare_indicators = [
        'checking your browser', 'cf-ray', 'cloudflare', 'challenges.cloudflare.com',
        '__cfduid', 'cf_clearance', 'cloudflare-static'
    ]
    if any(indicator in text_lower or indicator in headers_str for indicator in cloudflare_indicators):
        protections.append('Cloudflare')
    
    # Check for reCAPTCHA v3
    recaptcha_v3_indicators = [
        'recaptcha/releases/v3', 'grecaptcha.execute', 'recaptcha-v3',
        'data-sitekey', 'recaptcha/api.js'
    ]
    if any(indicator in text_lower for indicator in recaptcha_v3_indicators):
        if 'grecaptcha.execute' in text_lower or 'v3' in text_lower:
            protections.append('reCAPTCHA v3')
    
    # Check for reCAPTCHA v2
    recaptcha_v2_indicators = [
        'g-recaptcha', 'recaptcha/api.js', 'protected by reCAPTCHA', 
        'recaptcha-checkbox', 'recaptcha-anchor'
    ]
    if any(indicator in text_lower for indicator in recaptcha_v2_indicators):
        if 'g-recaptcha' in text_lower or 'checkbox' in text_lower:
            protections.append('reCAPTCHA v2')
    
    # Check for other protections
    other_protections = [
        ('hcaptcha', 'hCaptcha'),
        ('turnstile', 'Cloudflare Turnstile'),
        ('funcaptcha', 'FunCaptcha'),
        ('geetest', 'GeeTest'),
        ('anti-bot', 'Anti-Bot'),
        ('ddos-guard', 'DDoS-Guard'),
        ('incapsula', 'Incapsula'),
        ('sucuri', 'Sucuri')
    ]
    
    for indicator, name in other_protections:
        if indicator in text_lower or indicator in headers_str:
            protections.append(name)
    
    # Return combined protections or 'Maybe clean'
    if protections:
        return ', '.join(protections)
    return 'Maybe clean'

def check_for_platform(text):
    platform_signatures = {
        'woocommerce': ['woocommerce', 'wc-cart', 'wc-ajax', 'wc-admin'],
        'magento': ['magento', 'mageplaza', 'mage/cookies'],
        'shopify': ['shopify', 'myshopify', 'shopify-section'],
        'prestashop': ['prestashop', 'addons.prestashop'],
        'opencart': ['opencart', 'route=common/home'],
        'bigcommerce': ['bigcommerce', 'stencil', 'bigcommerce-stencil'],
        'wordpress': ['wp-content', 'wp-includes', 'wordpress'],
        'drupal': ['drupal', 'sites/all', 'drupal.js'],
        'joomla': ['joomla', 'index.php?option=com_', 'joomla!'],
        'squarespace': ['squarespace-cdn', 'static.squarespace.com'],
        'wix': ['wix.com', 'wixstatic.com', 'wix-code'],
        'weebly': ['weebly.com', 'weeblycloud.com'],
        'webflow': ['webflow', 'webflow.io', 'webflow.com'],
        'laravel': ['laravel_session', 'laravel', 'csrf-token'],
        'django': ['csrfmiddlewaretoken', 'django', '__admin'],
        'react': ['react', 'reactjs', '_app.js'],
        'angular': ['angular', 'ng-app', 'angular.js'],
        'vue': ['vue.js', 'vuejs', '__nuxt']
    }

    text_lower = text.lower()
    for platform, signatures in platform_signatures.items():
        if any(sig in text_lower for sig in signatures):
            return platform.capitalize()
    
    return 'Unknown'

def format_single_result(result):
    gateways = ', '.join(result['payment_gateways']) if result['payment_gateways'] else 'None'
    error_msg = f" | Error: {result['error']}" if result['error'] else ""
    
    return (
        f"{result['url']} | {result['protection']} | {gateways} | "
        f"{result['platform']} | {result['time_taken']}s{error_msg}"
    )

def format_analysis_header():
    return (
        
        f"⚡ ADVANCED SITE ANALYSIS SYSTEM ⚡\n"
        f"🔥 Owner: @cheetax1 🔥\n"       
        f"📋 Format: URL | Protection | Gateways | Platform | Time\n"
        f"🛡️ Detections: reCAPTCHA v2/v3, Cloudflare, hCaptcha+\n"
        
    )

def handle_my_account_command(chat_id, replied_message):
    if not replied_message or 'document' not in replied_message:
        send_message(chat_id, "❌ You must reply to a file with this command.")
        return

    file_id = replied_message['document']['file_id']
    info = requests.get(URL + 'getFile', params={'file_id': file_id}).json()
    path = info['result']['file_path']
    file_url = f'https://api.telegram.org/file/bot{TOKEN}/{path}'
    file_data = requests.get(file_url).content

    for encoding in ['utf-8', 'latin-1', 'windows-1252']:
        try:
            lines = file_data.decode(encoding).splitlines()
            break
        except UnicodeDecodeError:
            continue
    else:
        send_message(chat_id, "❌ Error decoding file. Use UTF-8, Latin-1, or Windows-1252.")
        return

    updated_urls = []
    for line in lines:
        url = line.strip()
        if url and url.startswith(('http://', 'https://')):
            try:
                domain = url.split('/')[2]
                scheme = url.split(':')[0]
                new_url = f"{scheme}://{domain}/my-account"
                updated_urls.append(new_url)
            except:
                continue

    if not updated_urls:
        send_message(chat_id, "⚠️ No valid URLs found.")
        return

    send_file(chat_id, '\n'.join(updated_urls), filename='my_account_urls.txt')

def handle_file(chat_id, file_content):
    for encoding in ['utf-8', 'latin-1', 'windows-1252']:
        try:
            urls = file_content.decode(encoding).splitlines()
            break
        except UnicodeDecodeError:
            continue
    else:
        error_msg = (
            
            "🚫 FILE ENCODING ERROR 🚫\n"
            
            "📝 Please use one of these encodings:\n"
            "• UTF-8 (Recommended)\n"
            "• Latin-1\n"
            "• Windows-1252\n\n"
            "💡 Try re-saving your .txt file with UTF-8 encoding"
        )
        send_message(chat_id, error_msg)
        return
    
    context_data[chat_id] = [u.strip() for u in urls if u.strip()]
    valid_urls = len(context_data[chat_id])
    
    success_msg = (
        f"✅ Task Approved\n"
        f"🎉 FILE UPLOADED SUCCESSFULLY! 🎉\n"
        f"📊 Total URLs found: {valid_urls}\n"
        f"🚀 Ready for analysis!\n\n"
        f"⚡ Type /url to start lightning-fast analysis\n"
        f"🔥 Advanced detection system ready!"
    )
    send_message(chat_id, success_msg)

def handle_url_command(chat_id, text):
    if text.startswith('/url '):
        single_url = text.split(' ', 1)[1]
        result = analyze_site(single_url)
        formatted_result = format_analysis_header() + format_single_result(result)
        send_message(chat_id, formatted_result)
    else:
        urls = context_data.get(chat_id)
        if not urls:
            send_message(chat_id, "❌ No URLs uploaded. Send a .txt file first.")
            return

        # Send initial message
        initial_message = (
            format_analysis_header() + 
            f"⚡ ANALYSIS ENGINE STARTING UP! ⚡\n"
            f"📊 Total URLs to analyze: {len(urls)}\n"
            f"🔥 Advanced detection systems: ONLINE\n"
            f"⚡ Multi-threaded processing: ACTIVE\n\n"
            f"📈 Progress: 0/{len(urls)} (0%)\n"
            f"⏱️ Status: Initializing engines...\n"
            f"🎯 ETA: Calculating..."
        )
        message_id = send_message(chat_id, initial_message)
        
        start_time = datetime.now()
        results = []
        completed = 0
        total = len(urls)
        
        def worker(url):
            nonlocal completed
            result = analyze_site(url)
            with lock:
                completed += 1
                elapsed = datetime.now() - start_time
                
                # Update progress every 5 completions or at milestones for better spacing
                if completed % 5 == 0 or completed in [1, 2, 3] or completed == total:
                    progress_percent = (completed / total) * 100
                    progress_bar = "█" * int(progress_percent // 5) + "░" * (20 - int(progress_percent // 5))
                    
                    if completed > 1:
                        avg_time_per_url = elapsed.total_seconds() / completed
                        remaining_time = int((total - completed) * avg_time_per_url)
                        eta_text = f"⏱️ ETA: {remaining_time}s remaining"
                        speed_text = f"🚀 Speed: {avg_time_per_url:.2f}s per URL"
                    else:
                        eta_text = "⏱️ ETA: Calculating..."
                        speed_text = "🚀 Speed: Analyzing..."
                    
                    progress_message = (
                        format_analysis_header() +
                        
                        f"🔥 ANALYSIS IN PROGRESS! 🔥\n"                        
                        f"📊 Progress: {completed}/{total} ({progress_percent:.1f}%)\n"
                        f"📈 [{progress_bar}] {progress_percent:.1f}%\n\n"
                        f"{eta_text}\n"
                        f"{speed_text}\n"
                        f"🎯 Status: {'FINALIZING' if completed == total else 'SCANNING'}\n\n"
                        +
                        '\n'.                     join([format_single_result(analyze_site(urls[i])) for i in range(max(0, completed-3), completed)])
                    )
                    
                    if message_id:
                        edit_message(chat_id, message_id, progress_message)
            
            return format_single_result(result)

        with ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(worker, urls))

        # Final results
        total_time = (datetime.now() - start_time).seconds
        successful_scans = len([r for r in results if 'Error:' not in r])
        failed_scans = total - successful_scans
        
        final_message = (
            format_analysis_header() +
            f"🎉 Task Completed"
            f"✅ ANALYSIS COMPLETED! SUCCESS! ✅\n"
            f"📊 Total URLs processed: {len(urls)}\n"
            f"✅ Successful scans: {successful_scans}\n"
            f"❌ Failed scans: {failed_scans}\n"
            f"⏱️ Total time: {total_time}s\n"
            f"🚀 Average speed: {total_time/len(urls):.2f}s per URL\n\n"
        )
        
        if len(results) > 8:
            final_message += f"\n{'═' * 45}\n📁 Complete results sent as file below! 📁"
        
        if message_id:
            edit_message(chat_id, message_id, final_message)
        
        # Send full results as file
        full_results = format_analysis_header() + '\n'.join(results)
        send_file(chat_id, full_results, 'analysis_results.txt')

def handle_start_command(chat_id):
    welcome_msg = (
        " 🚀 ADVANCED SITE ANALYSIS BOT ONLINE! 🚀\n"
        "💎 Created by @cheetax1 💎\n"
        "📱 HOW TO USE:\n"
        "1️⃣ Upload .txt file with URLs\n"
        "2️⃣ Use /url to start bulk analysis\n"
        "3️⃣ For single check: /url https://example.com\n\n"
        "🔍 WHAT I DETECT:\n"
        "🛡️ Protection: reCAPTCHA v2/v3, Cloudflare, hCaptcha\n"
        "💳 Gateways: PayPal, Stripe, Square, Amazon Pay+\n"
        "🌐 Platforms: WooCommerce, Shopify, Magento+\n\n"
        "⚡ Lightning fast with real-time progress updates!\n"
        "Type /cmds for all commands 📋"
    )
    send_message(chat_id, welcome_msg)

def handle_cmds_command(chat_id):
    commands_msg = (
        
        " 🎯 AVAILABLE COMMANDS MENU 🎯\n"
        "🔥 @cheetax1 Bot System 🔥\n"
        "🔍 /url - Analyze uploaded URLs or single link\n"
        "   📝 Usage: /url https://example.com\n"
        "   📂 Or upload .txt file then type /url\n\n"
        "🏠 /my-account - Convert URLs to /my-account format\n"
        "   📁 Reply to a .txt file with this command\n\n"
        "📋 /cmds - Show this command menu\n\n"
        "🚀 /start - Show welcome message\n\n"
        "⚡ FEATURES:\n"
        "• Real-time progress updates\n"
        "• Advanced protection detection\n"
        "• 16+ payment gateway detection\n"
        "• Multi-platform identification\n"
        "• Lightning fast analysis\n\n"
        "💎 Created with ❤️ by @cheetax1"
    )
    send_message(chat_id, commands_msg)

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
                reply = message.get('reply_to_message')

                if text:
                    if text.startswith('/start'):
                        handle_start_command(chat_id)
                    elif text.startswith('/url'):
                        threading.Thread(target=handle_url_command, args=(chat_id, text)).start()
                    elif text.startswith('/cmds'):
                        handle_cmds_command(chat_id)
                    elif text.startswith('/my-account'):
                        threading.Thread(target=handle_my_account_command, args=(chat_id, reply)).start()
                elif doc:
                    file_id = doc['file_id']
                    info = requests.get(URL + 'getFile', params={'file_id': file_id}).json()
                    path = info['result']['file_path']
                    file_url = f'https://api.telegram.org/file/bot{TOKEN}/{path}'
                    file_data = requests.get(file_url).content
                    handle_file(chat_id, file_data)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nBot stopped by user.")
        sys.exit()
    except Exception:
        traceback.print_exc()
        sys.exit(1) 
