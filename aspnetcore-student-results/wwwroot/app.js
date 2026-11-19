const form = document.querySelector('#result-form');
const message = document.querySelector('#message');

async function request(path, options = {}) {
  const response = await fetch(path, options);
  if (!response.ok) {
    const problem = await response.json().catch(() => ({}));
    const details = Object.values(problem.errors ?? {}).flat().join(' ');
    throw new Error(details || problem.title || `Request failed (${response.status}).`);
  }
  return response.status === 204 ? null : response.json();
}

async function refresh() {
  const [summary, page] = await Promise.all([
    request('/api/results/summary'), request('/api/results?pageSize=100')
  ]);
  document.querySelector('#result-count').textContent = summary.totalResults;
  document.querySelector('#student-count').textContent = summary.totalStudents;
  document.querySelector('#average-score').textContent = summary.averageScore ?? '—';
  document.querySelector('#pass-rate').textContent = summary.passRatePercent == null ? '—' : `${summary.passRatePercent}%`;
  const body = document.querySelector('#results-body');
  body.replaceChildren();
  if (!page.items.length) {
    const row = body.insertRow();
    const cell = row.insertCell();
    cell.colSpan = 5;
    cell.textContent = 'No results yet. Add a synthetic result above.';
  }
  for (const result of page.items) {
    const row = body.insertRow();
    for (const value of [result.studentId, result.subject, result.score, result.passed ? 'Passed' : 'Below pass mark']) {
      row.insertCell().textContent = value;
    }
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'secondary';
    button.textContent = 'Delete';
    button.setAttribute('aria-label', `Delete ${result.studentId} ${result.subject}`);
    button.addEventListener('click', async () => {
      if (!window.confirm(`Delete ${result.studentId}'s ${result.subject} result?`)) return;
      button.disabled = true;
      try {
        await request(`/api/results/${result.id}`, { method: 'DELETE' });
        await refresh();
        message.textContent = 'Result deleted.';
      } catch (error) { message.textContent = error.message; }
      finally { button.disabled = false; }
    });
    row.insertCell().append(button);
  }
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  const button = form.querySelector('button');
  button.disabled = true;
  message.textContent = 'Saving…';
  try {
    await request('/api/results', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        studentId: form.elements.studentId.value,
        subject: form.elements.subject.value,
        score: Number(form.elements.score.value)
      })
    });
    form.reset();
    message.textContent = 'Result saved.';
    await refresh();
  } catch (error) { message.textContent = error.message; }
  finally { button.disabled = false; }
});

document.querySelector('#refresh').addEventListener('click', () => refresh().catch(error => { message.textContent = error.message; }));
refresh().catch(error => { message.textContent = error.message; });
