async function testTraineeFetch() {
  try {
    const res = await fetch('https://proprivilege-praedial-wesley.ngrok-free.dev/api/doctor/tickets/trainee', {
      headers: {
        'ngrok-skip-browser-warning': 'true'
      }
    });
    
    if (!res.ok) {
        console.error("HTTP ERROR", res.status, res.statusText);
        return;
    }
    
    const data = await res.json();
    console.log("TRAINEE DATA:", JSON.stringify(data, null, 2));
  } catch(e) {
      console.error(e);
  }
}
testTraineeFetch();
