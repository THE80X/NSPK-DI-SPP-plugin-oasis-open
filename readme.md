# NSPK-DI-SPP-oasis-open

## Написанные методы

# _checking_for_annotation
```python
def _checking_for_annotation(self, web_element: WebElement):
    try:
        result = web_element.find_element(By.TAG_NAME, 'p').find_element(By.TAG_NAME, 'strong')
        if result.text == '':
            return None
        else:
            return result.text
    except Exception:
        self.logger.warn(f'There is no annotation')
        return None
```
Данный метод был написан для того чтобы отдельно выделять аннотацию новости, которую впоследствии программа будет помещать в abstract.