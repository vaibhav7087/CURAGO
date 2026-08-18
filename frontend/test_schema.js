const fs = require('fs');
const dotenv = require('dotenv');
dotenv.config({ path: '.env.local' });

const supabaseUrl = process.env.VITE_SUPABASE_URL;
const supabaseKey = process.env.VITE_SUPABASE_ANON_KEY;

async function checkSchema() {
  const res = await fetch(`${supabaseUrl}/rest/v1/?apikey=${supabaseKey}`);
  const data = await res.json();
  
  if (data.definitions && data.definitions.orders) {
    console.log("ORDERS SCHEMA:");
    console.log(JSON.stringify(data.definitions.orders.properties, null, 2));
  } else {
    console.log("Orders table not found in public schema. Available tables:", Object.keys(data.definitions));
  }
}

checkSchema();
