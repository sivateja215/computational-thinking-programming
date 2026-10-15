# ------------------------------------------------------------
# Sample data (the "product records")
# ------------------------------------------------------------
products = [
    {'id': 1, 'category': 'electronics', 'price': 299, 'tags': {'wireless', 'audio'}},
    {'id': 2, 'category': 'electronics', 'price': 899, 'tags': {'gaming', 'laptop'}},
    {'id': 3, 'category': 'furniture',   'price': 150, 'tags': {'wooden', 'chair'}},
    {'id': 4, 'category': 'electronics', 'price': 59,  'tags': {'bluetooth', 'audio'}},
    {'id': 5, 'category': 'furniture',   'price': 220, 'tags': {'wooden', 'table'}},
]

target_category = 'electronics'
search_tags = ['audio', 'bluetooth']


# ------------------------------------------------------------
# 1) Naive nested-loop version (original approach)
# ------------------------------------------------------------
def find_products_nested(products, target_category, search_tags):
    results = []
    for product in products:
        if product['category'] == target_category:
            match = False
            for tag in product['tags']:
                for s_tag in search_tags:
                    if tag == s_tag:
                        match = True
            if match:
                results.append(product)
    return results


# ------------------------------------------------------------
# 2) Pythonic version: comprehension + set intersection
# ------------------------------------------------------------
def find_products(products, target_category, search_tags):
    search_tags = set(search_tags)
    return [
        product for product in products
        if product['category'] == target_category
        and product['tags'] & search_tags
    ]


# ------------------------------------------------------------
# Run and print results
# ------------------------------------------------------------
if __name__ == '__main__':
    print(f"Target category: {target_category}")
    print(f"Search tags: {search_tags}\n")

    print("Method 1 - Nested loops:")
    for p in find_products_nested(products, target_category, search_tags):
        print(f"  {p}")

    print("\nMethod 2 - Comprehension + set intersection:")
    for p in find_products(products, target_category, search_tags):
        print(f"  {p}")
