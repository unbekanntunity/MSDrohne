from Communication import custom_threads

thread = custom_threads.DisposableThread()
thread.events.add_event(lambda: print("aa"))
thread.start()

thread.join()