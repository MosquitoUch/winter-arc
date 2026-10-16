package com.mosquitouch.winterarc;

import android.content.Context;
import android.content.SharedPreferences;
import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;

/** Nimmt die Widget-Daten aus der Web-App entgegen und aktualisiert das Homescreen-Widget. */
@CapacitorPlugin(name = "WidgetBridge")
public class WidgetBridgePlugin extends Plugin {

    @PluginMethod
    public void update(PluginCall call) {
        JSObject data = call.getData();
        Context ctx = getContext();
        SharedPreferences prefs = ctx.getSharedPreferences(WinterArcWidget.PREFS, Context.MODE_PRIVATE);
        prefs.edit().putString(WinterArcWidget.KEY, data.toString()).apply();
        WinterArcWidget.updateAll(ctx);
        call.resolve();
    }
}
