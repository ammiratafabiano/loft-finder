from costants import UrlWatchType
from services.storage import storage

# for user in storage.load():
#     print(user.username, user.chat_id)
#     for watch in user.watchlist:
#         print("- ", watch.source, watch.url)
#     print("----")
#
# print("\n\n---- START edit\n\n")
#
# for user in storage.load():
#     print(user.username, user.chat_id)
#     for watch in user.watchlist:
#         print(f"\n{watch.source}\n")
#         if watch.source == UrlWatchType.SUBITO.value and "monza" in watch.province.lower():
#             print(f"\n{watch.province}\n")
#             watch.province = "Monza"
#             print(f"\nnow -> {watch.province}\n")
#         if watch.source == UrlWatchType.CASADAPRIVATO.value and "monza" in watch.province.lower():
#             print(f"\n{watch.province}\n")
#             watch.province = "Monza Brianza"
#             print(f"\nnow -> {watch.province}\n")
#         if watch.source == UrlWatchType.IDEALISTA.value and "monza" in watch.province.lower():
#             print(f"\n{watch.province}\n")
#             watch.province = "Monza Brianza"
#             print(f"\nnow -> {watch.province}\n")
#         watch.set_url()
#         print("\n")
# storage.save()
#
# print("\n\n---- END edit\n\n")

for user in storage.load():
    print(user.username, user.chat_id)
    for watch in user.watchlist:
        print("- ", watch.source)
        print(watch.url)
        print(f"attempts {watch.remaining_attempts}/{watch.attempts}")
    print("----")
