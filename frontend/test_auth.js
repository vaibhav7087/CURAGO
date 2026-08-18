import { createClient } from '@supabase/supabase-js'

const supabaseUrl = "https://fxywkkawfsiarjpdfdvk.supabase.co"
const supabaseAnonKey = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ4eXdra2F3ZnNpYXJqcGRmZHZrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzE3MDE5MDcsImV4cCI6MjA4NzI3NzkwN30.qsCClsPJNh8IGHAA-ACMJDKs3BfuZyKBhZ6wehOABSM"

const supabase = createClient(supabaseUrl, supabaseAnonKey)

async function testAuth() {
  console.log('Logging in as doctor@hospital.com...');
  const { data: authData, error: authError } = await supabase.auth.signInWithPassword({
    email: 'doctor@hospital.com',
    password: 'Doctor123'
  });

  if (authError) {
    console.error('Login Error:', authError.message);
    return;
  }
  
  console.log('Login Success! User ID:', authData.user.id);
  
  const { data: tickets, error: ticketError } = await supabase.from('tickets').select('*');
  if (ticketError) {
    console.log('Tickets Error:', ticketError);
  } else {
    console.log(`Tickets returned: ${tickets.length}`);
  }

  const { data: inventory, error: inventoryError } = await supabase.from('inventory').select('*');
  if (inventoryError) {
    console.log('Inventory Error:', inventoryError);
  } else {
    console.log(`Inventory returned: ${inventory.length}`);
  }
}

testAuth();
