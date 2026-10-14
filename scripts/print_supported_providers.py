from repodoctor.llm.factory import SUPPORTED_PROVIDERS

print("Supported RepoDoctor providers:")
for provider in SUPPORTED_PROVIDERS:
    print(f"- {provider}")
