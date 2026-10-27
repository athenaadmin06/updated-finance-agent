import { Component } from '@angular/core';
import { environment } from '../environments/environment.prod';
@Component({ selector: 'app-root', template: '<h1>{{ url }}</h1>' })
export class AppComponent { url = environment.apiUrl; }
