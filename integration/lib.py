from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
import time


def login(selenium, app_domain, device_user, device_password):

    selenium.open_app("/wp-login.php")
    selenium.wait_or_screenshot(EC.element_to_be_clickable((By.ID, 'user_login')))

    user = selenium.find_by_id("user_login")
    user.send_keys(device_user)
    password = selenium.find_by_id("user_pass")
    password.send_keys(device_password)
    selenium.screenshot('login')
    password.send_keys(Keys.RETURN)
    
    time.sleep(10)
    
    selenium.screenshot('login-complete')
