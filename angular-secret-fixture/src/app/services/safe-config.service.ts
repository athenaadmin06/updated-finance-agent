import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface AppPublicConfig {
  apiUrl: string;
  theme: string;
}

/**
 * Decoy Service: Demonstrates compliant, safe runtime configuration loading.
 * No secrets hardcoded. Scanners should NOT flag this service.
 */
@Injectable({
  providedIn: 'root',
})
export class SafeConfigService {
  private config: AppPublicConfig | null = null;

  constructor(private http: HttpClient) {}

  public loadConfig(): Observable<AppPublicConfig> {
    // Safely loads non-sensitive configuration from an assets file or runtime endpoint
    return this.http.get<AppPublicConfig>('/assets/config.json');
  }

  public getConfig(): AppPublicConfig | null {
    return this.config;
  }
}

