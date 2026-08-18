import { createClient } from '@supabase/supabase-js';

const supabaseUrl = 'https://fxywkkawfsiarjpdfdvk.supabase.co';
const supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ4eXdra2F3ZnNpYXJqcGRmZHZrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzE3MDE5MDcsImV4cCI6MjA4NzI3NzkwN30.qsCClsPJNh8IGHAA-ACMJDKs3BfuZyKBhZ6wehOABSM';
const supabase = createClient(supabaseUrl, supabaseKey);

async function testTrainees() {
  const { data, error } = await supabase
    .from('tickets')
    .select('*')
    .not('assignedTraineeId', 'is', null);

  if (error) {
    console.error("Error:", error);
  } else {
    console.log("Total trainee tickets:", data.length);
    if (data.length > 0) {
      console.log("Status array:", data.map(d => d.ticketStatus));
    }
  }
}

testTrainees();
