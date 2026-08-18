import * as dotenv from 'dotenv';
dotenv.config({ path: '.env.local' });

const supabaseUrl = process.env.VITE_SUPABASE_URL;
const supabaseKey = process.env.VITE_SUPABASE_ANON_KEY;

async function checkSchema() {
  const res = await fetch(`${supabaseUrl}/rest/v1/?apikey=${supabaseKey}`);
  const data = await res.json();
  
  if (data.definitions && data.definitions.orders) {
    console.log("ORDERS SCHEMA:");
    console.log(JSON.stringify(data.definitions.orders.properties, null, 2));
  } else if (data.definitions) {
    console.log("Orders table not found. Available tables:", Object.keys(data.definitions));
  } else {
    console.log("Failed to fetch schema", data);
  }
}

checkSchema();
