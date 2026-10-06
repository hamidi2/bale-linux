# Push به GitHub (hamidi2)
1. در github.com با اکانت hamidi2 یک ریپوی خالی به نام bale-linux بساز (بدون README).
2. دستورات:
   cd ~/code/bale-linux
   git remote add origin https://github.com/hamidi2/bale-linux.git
   git push -u origin master
3. اگر پسورد خواست: از Personal Access Token استفاده کن (پسورد معمولی قبول نمی‌کند):
   GitHub → Settings → Developer settings → Personal access tokens → Generate (scope: repo)
4. راه ssh (بدون توکن): کلید عمومی ~/.ssh/id_rsa.pub را در Settings → SSH keys ثبت کن و:
   git remote set-url origin git@github.com:hamidi2/bale-linux.git
   git push -u origin master
