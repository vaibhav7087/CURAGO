import { createClient } from '@supabase/supabase-js';

const supabaseUrl = 'https://fxywkkawfsiarjpdfdvk.supabase.co';
const supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ4eXdra2F3ZnNpYXJqcGRmZHZrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzE3MDE5MDcsImV4cCI6MjA4NzI3NzkwN30.qsCClsPJNh8IGHAA-ACMJDKs3BfuZyKBhZ6wehOABSM';
const supabase = createClient(supabaseUrl, supabaseKey);

async function testVitals() {
  const testTicketId = '77777777-7777-7777-7777-777777777777'; // existing ID from dump

  const { error } = await supabase
    .from('tickets')
    .update({ vitalsData: { hr: "100", dia: "80", sys: "120", spo2: "99", temp: "98.6" } })
    .eq('ticketId', testTicketId)
    .select();

  if (error) {
    console.error("ERROR UPDATING VITALS:", JSON.stringify(error, null, 2));
  } else {
    console.log("SUCCESSFULLY UPDATED VITALS.");
  }
}

testVitals();
