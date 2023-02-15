
def author_filter_list(cookbook):
    a_list = []
    for recipe in cookbook:
        author = [recipe.author_name, recipe.author_url]
        if author not in a_list:
            a_list.append(author)

    return a_list


def source_filter_list(cookbook):
    s_list = []
    for recipe in cookbook:
        source = [recipe.publisher_name, recipe.publisher_url]
        if source not in s_list:
            s_list.append(source)

    return s_list


def cuisine_filter_list(cookbook):
    cu_list = []
    for recipe in cookbook:
        cuisine = [recipe.cuisine]
        if cuisine not in cu_list:
            cu_list.append(cuisine)

    return cu_list