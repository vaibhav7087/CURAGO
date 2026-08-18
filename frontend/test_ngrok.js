async function testFetch() {
  try {
    const res = await fetch('https://proprivilege-praedial-wesley.ngrok-free.dev/api/doctor/tickets/general', {
      headers: {
        'ngrok-skip-browser-warning': 'true'
      }
    });
    
    if (!res.ok) {
        console.error("HTTP ERROR", res.status, res.statusText);
        return;
    }
    
    const data = await res.json();
    console.log("Data from Ngrok:", JSON.stringify(data, null, 2));
  } catch(e) {
      console.error(e);
  }
}
testFetch();
