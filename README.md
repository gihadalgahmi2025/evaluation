## Evaluation

 **Frappe v16** 
### Fresh install

```bash
cd ~/frappe-bench
bench get-app /path/to/evaluation
bench --site site1.local install-app evaluation
bench build --app evaluation
bench --site site1.local migrate
bench restart
```
