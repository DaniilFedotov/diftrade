import time


def cache(cache_list, current_price, size):
    """Создает кэш, размер которого задан параметром size,
    определяемым длиной кэшируемого участка на временном графике.
    """
    if len(cache_list) == int(size):
        new_cache_list = []
        for j in range(1, int(size)):
            new_cache_list.append(cache_list[j])
        new_cache_list.append(current_price)
        return new_cache_list
    cache_list.append(current_price)
    return cache_list


def cache_new(cache_list, current_price, size):
    """Создает кэш, размер которого задан параметром size,
    определяемым длиной кэшируемого участка на временном графике.
    """
    if len(cache_list) == int(size):
        cache_list.remove(cache_list[0])
    cache_list.append(current_price)
    return cache_list


start = time.time()
cache_level = []
for i in range(1, 600):
    cache_level = cache(cache_level, i, 400)
    print(cache_level)
    i += 1
end = time.time() - start
print(end)
