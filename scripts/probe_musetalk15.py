from gradio_client import Client

SPACE = "henrybit/musetalk-1-5"
print(f"PROBE_START space={SPACE}", flush=True)
client = Client(SPACE, verbose=True)
print("CLIENT_CONNECTED", flush=True)
client.view_api(all_endpoints=True)
print("PROBE_OK", flush=True)
