import asyncio
import httpx
import json

async def test_vapi_webhooks():
    # 1. Test the Tool Call (RAG Search)
    print("\n--- Testing Vapi RAG Tool Call ---")
    tool_payload = {
        "message": {
            "type": "tool-calls",
            "toolWithToolCallList": [
                {
                    "tool": {"name": "search_medical_guidelines"},
                    "toolCall": {
                        "id": "call_123",
                        "function": {
                            "name": "search_medical_guidelines",
                            "arguments": {"query": "dengue fever"}
                        }
                    }
                }
            ]
        }
    }
    
    async with httpx.AsyncClient() as client:
        try:
            res = await client.post("http://localhost:8002/api/rag/search", json=tool_payload)
            print("Status Code:", res.status_code)
            print("Response:", res.json())
        except Exception as e:
            print(f"Failed to reach backend (is it running on 8002?): {e}")

    # 2. Test the End of Call Webhook (Ticket Creation)
    print("\n--- Testing Vapi End-of-Call Report ---")
    end_call_payload = {
        "message": {
            "type": "end-of-call-report",
            "call": {
                "id": "vapi_call_789",
                "customer": {"number": "+15714061122"}
            },
            "transcript": "Patient says they have high fever and body ache.",
            "analysis": {
                "structuredData": {
                    "patient_name": "Ramesh Kumar",
                    "severity": "Medium",
                    "symptoms": "High fever, body ache",
                    "age": 45,
                    "gender": "Male",
                    "village": "Pune"
                }
            }
        }
    }

    async with httpx.AsyncClient() as client:
        try:
            res = await client.post("http://localhost:8002/api/webhook/end-call", json=end_call_payload)
            print("Status Code:", res.status_code)
            print("Response:", res.json())
        except Exception as e:
            print(f"Failed to reach backend: {e}")

if __name__ == "__main__":
    asyncio.run(test_vapi_webhooks())
