import { Component, OnInit } from '@angular/core';
import { HealthService, HealthStatus } from './services/health.service';

@Component({
  selector: 'app-root',
  template: `
    <div style="font-family: sans-serif; padding: 20px;">
      <h1>Angular Finance Dashboard</h1>
      <p>Health API Status: <strong>{{ status?.status || 'Checking...' }}</strong></p>
      <pre>{{ status | json }}</pre>
    </div>
  `,
})
export class AppComponent implements OnInit {
  public status: HealthStatus | null = null;

  constructor(private healthService: HealthService) {}

  ngOnInit(): void {
    this.healthService.checkHealth().subscribe({
      next: (data) => (this.status = data),
      error: (err) => console.error('Health check failed', err),
    });
  }
}

