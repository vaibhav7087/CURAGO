import { createClient } from '@supabase/supabase-js';

// The values directly pasted here to bypass dotenv issues
const supabaseUrl = 'https://fxywkkawfsiarjpdfdvk.supabase.co';
const supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ4eXdra2F3ZnNpYXJqcGRmZHZrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzE3MDE5MDcsImV4cCI6MjA4NzI3NzkwN30.qsCClsPJNh8IGHAA-ACMJDKs3BfuZyKBhZ6wehOABSM';

async function checkSchema() {
  const supabase = createClient(supabaseUrl, supabaseKey);
  const { data, error } = await supabase
    .from('orders')
    .select('*')
    .limit(1);

  if (error) {
    console.error("Error reading orders table:", error.message);
  } else {
    console.log("SUCCESS. Columns available in 'orders':", Object.keys(data[0] || {}));
  }
}

checkSchema();
